import asyncio
import json
import logging
from stagehand import StagehandConfig, Stagehand
from app.testcase.test_case import load_testcase
from app import Config
import re
import time

logger = logging.getLogger(Config.APP_NAME)


class MainService:
    def __init__(self):
        self.recorded_actions = []  # сюда пишем действия
        self.cache_file = "./storage/cached_steps.json"
        self.test_case = None
        

    async def process(self, mode="ai"):
        logger.debug(f"Start QA automation, mode={mode}")

        # Load steps from steps.txt
        steps_file = "./storage/steps.txt"
        
        logger.info(f"Loading steps from {steps_file}")
        with open(steps_file, "r", encoding="utf-8") as f:
            steps_text = f.read()

        # use test_case.py to parse steps.txt

        self.test_case = load_testcase(steps_file)
        action_steps = [step.text for step in self.test_case.steps]
        print(action_steps)

        logger.info(f"Loaded {len(action_steps)} action steps from {steps_file}")

        # Load test data
        data_path = "./storage/data.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data_vars = json.load(f)

        # Init Stagehand
        config = StagehandConfig(
            env="LOCAL",
            model_name="google/gemini-2.5-flash",
            model_api_key=Config.GEMINI_API_KEY,
            verbose=2
        )

        stagehand = Stagehand(config=config)
        await stagehand.init()
        page = stagehand.page
        agent = stagehand.agent  # Access the agent for fallback reasoning

        await page.set_viewport_size({
            "width": 1280,
            "height": 980
        })

        # Open your main app page
        await page.goto("https://127.0.0.1:4443/")
        logger.info("Initial page loaded")

        # Mode: REPLAY (без агента)
        if mode == "replay":
            return await self.replay_mode(stagehand)

        # AI Mode: Execute each action using page.act()
        logger.info("Starting AI mode - executing actions with page.act()")
        
        executed_actions = []
        
        for i, action_step in enumerate(action_steps, 1):
            try:
                logger.info(f"[{i}/{len(action_steps)}] Executing: {action_step}")
                
                # Replace placeholders with actual values from data.json
                action_instruction = action_step
                for key, value in data_vars.items():
                    placeholder = f"{{{{{key}}}}}"
                    if placeholder in action_instruction:
                        action_instruction = action_instruction.replace(placeholder, str(value))
                
                # Take screenshot before action
                screenshot_before = f"./storage/screenshots/step_{i:03d}_before.png"
                try:
                    await page.screenshot(path=screenshot_before)
                    logger.debug(f"Screenshot saved: {screenshot_before}")
                except Exception as e:
                    logger.warning(f"Could not save before screenshot: {e}")
                
                # Determine execution method based on action type
                # Fill actions: use page.act() (faster, more reliable for form inputs)
                # Click actions: use page.act() with useVision=True (more intelligent, handles complex UI better)
                is_click_action = action_instruction.lower().startswith('click') or 'click' in action_instruction.lower() or action_instruction.lower().startswith('press') or 'press' in action_instruction.lower()
                is_expect_action = action_instruction.lower().startswith('expect')
                is_wait_action = action_instruction.lower().startswith('wait')
               
                if is_expect_action:
                    # Use page.observe for expect actions (assertions/validations)
                    logger.debug(f"Calling page.observe() for expect action: {action_instruction}")
                    result = await page.observe(action_instruction)
                    logger.info(f"🔎 Observe executed for expect: {result}")
                elif is_click_action:
                    # Use page.act with vision for click actions (more intelligent)
                    logger.debug(f"Calling page.act() with vision for click action: {action_instruction}")
                    result = await page.act(action_instruction, useVision=True)
                    logger.info(f"🤖 Vision-based act executed click: {result}")
                elif is_wait_action:
                    logger.debug(f"Calling page.wait() for wait action: {action_instruction}")
                    await self.execute_wait_step(page, action_instruction)
                    logger.info(f"⏳ Act executed wait: {result}")
                else:
                    # Use page.observe for other actions
                    logger.debug(f"Calling page.act() with: {action_instruction}")
                    result = await page.act(action_instruction)
                # Validate that action was actually executed
                action_succeeded = False
                error_message = None
                
                # Log the raw result for debugging
                logger.debug(f"Raw result type: {type(result)}")
                logger.debug(f"Raw result type name: {type(result).__name__}")
                logger.debug(f"Raw result repr: {repr(result)}")
                logger.debug(f"Raw result str: {str(result)}")
                logger.debug(f"Raw result dir: {[attr for attr in dir(result) if not attr.startswith('_')]}")
                
                # Check for string representation indicating failure (fallback check)
                result_str = str(result)
                if "success=False" in result_str or "No observe results found" in result_str:
                    error_message = f"Action failed based on string representation: {result_str}"
                    logger.error(f"❌ {error_message}")
                
                # Check for ActResult object (Stagehand's result type)
                elif hasattr(result, 'success'):
                    # This is an ActResult object
                    logger.debug(f"Detected ActResult object with success={result.success}")
                    if result.success:
                        action_succeeded = True
                        logger.debug(f"ActResult: success=True")
                    else:
                        error_message = f"ActResult: success=False, message='{getattr(result, 'message', 'No message')}'"
                        logger.error(f"❌ {error_message}")
                        
                elif result is None:
                    error_message = "Action returned None - no element found or action failed"
                    
                elif isinstance(result, dict):
                    # Check if it's a dict with empty elements
                    if 'elements' in result:
                        elements = result.get('elements', [])
                        if len(elements) == 0:
                            error_message = "Action returned empty elements list - element not found on page"
                        else:
                            action_succeeded = True
                            logger.debug(f"Action found {len(elements)} element(s) in dict")
                    else:
                        action_succeeded = True  # Assume success for other dict types
                        
                elif isinstance(result, list):
                    if len(result) == 0:
                        error_message = "Action found 0 elements - element not found on page"
                    else:
                        # Check if it's a list of ObserveResult objects
                        if all(hasattr(item, 'selector') for item in result):
                            action_succeeded = True
                            logger.debug(f"Action found {len(result)} element(s): {[getattr(r, 'selector', str(r)) for r in result]}")
                        else:
                            action_succeeded = True  # Other list types
                            
                elif hasattr(result, '__len__') and len(result) == 0:
                    error_message = "Action result is empty - element not found on page"
                    
                else:
                    # For other result types, assume success if not None
                    action_succeeded = True
                    logger.debug(f"Action returned non-None result: {type(result)}")
                
                # Take screenshot after action
                screenshot_after = f"./storage/screenshots/step_{i:03d}_after.png"
                try:
                    await page.screenshot(path=screenshot_after)
                    logger.debug(f"Screenshot saved: {screenshot_after}")
                except Exception as e:
                    logger.warning(f"Could not save after screenshot: {e}")

                if is_expect_action and not action_succeeded:
                    logger.warning(f"⚠️ Expectation failed: {error_message}")
                    raise Exception(f"Expectation failed: {error_message}")   

                # If action failed, try agent fallback
                if not action_succeeded:
                    logger.warning(f"⚠️ Primary action failed: {error_message}")
                    logger.info("🤖 Attempting agent.execute() fallback for intelligent recovery...")
                    
                    try:
                        # Build a context-aware instruction for the agent
                        agent_instruction = f"""
You are a QA automation recovery agent.

The following UI action just failed:

Action: {action_instruction}
Error: {error_message}

Your task is to recover and complete ONLY the failed action above.

Rules (must follow strictly):
- Treat the action as complete as soon as the immediate intent of the action is satisfied.
- Do NOT infer, chain, or continue to follow-up steps.
- Do NOT perform any action that represents a logical "next step" beyond the original action.
- If the action opens a menu, dialog, dropdown, or wizard, STOP once it is visible.
- If the action is ambiguous, choose the minimal interaction that best matches the action text.

Recovery strategies (try in order, up to max_steps):
1. Locate equivalent elements (text, icon, role, aria-label, tooltip, proximity)
2. Check for alternative UI representations (icon vs text, toolbar vs menu)
3. Check state issues (hidden, disabled, loading, collapsed, modal)
4. Scroll to reveal the target
5. Try a different interaction method (keyboard, focus + Enter, click by coordinates)
6. Interact with required parent or wrapper elements ONLY if necessary to perform the action

STOP IMMEDIATELY after the single action is completed.

If the action cannot be completed, provide diagnostics ONLY (do not act further):
- What elements ARE visible
- What the page state appears to be
- Why the target action cannot be completed
- What minimal alternative action might enable it

Do not proceed to any other steps.
"""
                        
                        # Initialize agent with computer use model for advanced reasoning
                        agent = stagehand.agent(
                            model="gemini-2.5-computer-use-preview-10-2025",
                            instructions="You are an intelligent QA recovery agent. Use advanced reasoning to complete failed UI actions.",
                            options={"apiKey": Config.GEMINI_API_KEY}
                        )
                        
                        # Use agent.execute for multi-step reasoning and recovery
                        logger.debug(f"Agent instruction: {agent_instruction}")
                        agent_result = await agent.execute(
                            instruction=agent_instruction,
                            max_steps=10,  # Allow up to 10 reasoning steps
                            auto_screenshot=True,
                            highlightCursor=False
                        )
                        
                        logger.info(f"🤖 Agent.execute() result: {agent_result}")
                        
                        # Take screenshot after agent attempt
                        screenshot_agent = f"./storage/screenshots/step_{i:03d}_agent_fallback.png"
                        try:
                            await page.screenshot(path=screenshot_agent)
                            logger.debug(f"Agent fallback screenshot saved: {screenshot_agent}")
                        except Exception as e:
                            logger.warning(f"Could not save agent screenshot: {e}")
                        
                        # Check if agent succeeded
                        # agent.execute() returns an ExecuteResult object with actions list
                        agent_succeeded = False
                        agent_diagnostics = None
                        
                        if hasattr(agent_result, 'actions'):
                            # ExecuteResult object from agent.execute()
                            actions_count = len(agent_result.actions)
                            logger.info(f"Agent executed {actions_count} actions during recovery")
                            
                            # Check if agent performed any actions
                            if actions_count > 0:
                                # Log the actions taken
                                for idx, action in enumerate(agent_result.actions, 1):
                                    action_info = str(action)
                                    logger.debug(f"  Agent action {idx}: {action_info}")
                                
                                # Check the last action for success
                                last_action = agent_result.actions[-1]
                                
                                # Check for success indicators in the action
                                if hasattr(last_action, 'success'):
                                    agent_succeeded = last_action.success
                                elif hasattr(last_action, 'status'):
                                    agent_succeeded = last_action.status == 'success'
                                else:
                                    # If no explicit success indicator, consider it successful if actions were taken
                                    agent_succeeded = True
                                
                                logger.info(f"Agent recovery result: {'Success' if agent_succeeded else 'Failed'}")
                            else:
                                logger.warning("Agent executed 0 actions - no recovery attempted")
                                agent_diagnostics = "Agent could not find any way to complete the action"
                        else:
                            # Fallback for unexpected result format
                            logger.warning(f"Unexpected agent result format: {type(agent_result)}")
                            agent_result_str = str(agent_result)
                            
                            # Check for explicit failure indicators
                            if "success=False" in agent_result_str or "No observe results found" in agent_result_str:
                                logger.error(f"❌ Agent fallback failed - detected failure in result: {agent_result_str}")
                                agent_succeeded = False
                            elif agent_result:
                                # Non-null result without clear failure indicator - consider partial success
                                agent_succeeded = True
                        
                        if agent_succeeded:
                            logger.info(f"✓ Agent.execute() fallback succeeded!")
                            
                            # Serialize agent actions for logging
                            agent_actions_log = []
                            if hasattr(agent_result, 'actions'):
                                for action in agent_result.actions:
                                    if hasattr(action, "model_dump"):
                                        agent_actions_log.append(action.model_dump())
                                    elif hasattr(action, "__dict__"):
                                        agent_actions_log.append(action.__dict__)
                                    else:
                                        agent_actions_log.append(str(action))
                            
                            executed_actions.append({
                                "step": i,
                                "instruction": action_instruction,
                                "original": action_step,
                                "status": "success_via_agent_execute",
                                "primary_error": error_message,
                                "agent_actions": agent_actions_log,
                                "agent_steps_count": len(agent_actions_log),
                                "screenshot_before": screenshot_before,
                                "screenshot_after": screenshot_agent
                            })
                        else:
                            logger.error(f"❌ Agent.execute() fallback failed")
                            
                            # Try to extract diagnostic info
                            if agent_diagnostics is None and hasattr(agent_result, 'actions'):
                                # Look for diagnostic information in the actions
                                diagnostics_parts = []
                                for action in agent_result.actions:
                                    action_str = str(action)
                                    if any(keyword in action_str.lower() for keyword in ['cannot', 'not found', 'failed', 'error']):
                                        diagnostics_parts.append(action_str)
                                agent_diagnostics = "; ".join(diagnostics_parts) if diagnostics_parts else "No specific diagnostics available"
                            
                            executed_actions.append({
                                "step": i,
                                "instruction": action_instruction,
                                "original": action_step,
                                "status": "failed_with_agent_execute",
                                "primary_error": error_message,
                                "agent_diagnostics": agent_diagnostics or str(agent_result),
                                "screenshot_error": screenshot_agent
                            })
                            raise Exception(f"Both primary action and agent.execute() fallback failed. Diagnostics: {agent_diagnostics}")
                    
                    except Exception as agent_error:
                        logger.error(f"❌ Agent fallback encountered error: {str(agent_error)}")
                        executed_actions.append({
                            "step": i,
                            "instruction": action_instruction,
                            "original": action_step,
                            "status": "failed",
                            "primary_error": error_message,
                            "agent_error": str(agent_error),
                            "screenshot_error": screenshot_after
                        })
                        raise Exception(f"Action failed and agent fallback errored: {agent_error}")
                else:
                    # Primary action succeeded
                    executed_actions.append({
                        "step": i,
                        "instruction": action_instruction,
                        "original": action_step,
                        "status": "success",
                        "result": str(result) if result else None,
                        "screenshot_before": screenshot_before,
                        "screenshot_after": screenshot_after
                    })
                    
                    logger.info(f"✓ Action completed: {action_instruction}")
                
                # Small delay between actions
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Action failed: {action_step}")
                logger.error(f"Error: {str(e)}")
                
                # Take error screenshot
                screenshot_error = f"./storage/screenshots/step_{i:03d}_error.png"
                try:
                    await page.screenshot(path=screenshot_error)
                    logger.error(f"Error screenshot saved: {screenshot_error}")
                except Exception as screenshot_error_ex:
                    logger.warning(f"Could not save error screenshot: {screenshot_error_ex}")
                
                executed_actions.append({
                    "step": i,
                    "instruction": action_instruction,
                    "original": action_step,
                    "status": "failed",
                    "error": str(e),
                    "screenshot_error": screenshot_error
                })
                
                # Stop execution on failure (don't continue with invalid state)
                logger.error("❌ Stopping execution due to action failure")
                break
        
        # Save executed actions log
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(executed_actions, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Executed actions log saved to {self.cache_file}")

        # Final screenshot
        screenshot_path = "final.png"
        await page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")

        await stagehand.close()
        logger.debug("End QA automation")

    def load_recorded_actions(self):
        with open(self.cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_wait_condition(self, step: str) -> dict:
        match = re.search(r'not\s+"([^"]+)"', step, re.IGNORECASE)
        return {
            "forbiddenValue": match.group(1) if match else "Running"
        }

    async def execute_wait_step(self, page, step: str):
        condition = self.parse_wait_condition(step)
        forbidden_value = condition["forbiddenValue"]

        # Treat @max_wait and @poll_interval as minutes
        cfg = self.test_case.config or {}
        max_wait_min = int(cfg.get("max_wait", 60))  # default 60 minutes
        poll_interval_min = float(cfg.get("poll_interval", 3))  # default 3 minutes

        timeout_ms = int(max_wait_min * 60 * 1000)  # minutes -> ms
        interval_ms = int(poll_interval_min * 60 * 1000)  # minutes -> ms

        start = time.time()
        last_status = None

        while (time.time() - start) * 1000 < timeout_ms:
            try:
                result = await page.observe(f"""
                Find the job status text that shows the current execution state (e.g., "Running (00:00:07)", "Success", "Failed").
                Return the text content of the status element.
                """)
            except Exception as e:
                logger.debug(f"observe failed: {e}; retrying...")
                await asyncio.sleep(interval_ms / 1000)
                continue

            if result is None or (isinstance(result, list) and len(result) == 0):
                logger.debug("No status element found, retrying...")
                await asyncio.sleep(interval_ms / 1000)
                continue

            # Extract status text from observe result (robust)
            status_text = await self.extract_status_text(page, result)
            if not status_text:
                logger.debug("Could not extract status text, retrying...")
                await asyncio.sleep(interval_ms / 1000)
                continue
            
            last_status = status_text
            logger.debug(f"Current status: {status_text}")
            
            # Check if status contains the forbidden value (e.g., "Running")
            is_still_forbidden = forbidden_value in status_text
            
            if not is_still_forbidden:
                # Status has changed from "Running" to something else (Success/Failed)
                logger.info(f"✓ Wait condition met. Status changed to: {status_text}")
                return

            # Status is still "Running", continue waiting
            logger.info(f"⏳ Still waiting... Current status: {status_text}")
            await asyncio.sleep(interval_ms / 1000)

        raise TimeoutError(
            f"Timeout waiting for backup job. Last status: {last_status}"
        )

    async def extract_status_text(self, page, result):
        """Robustly extract visible status text from observe results.
        - Supports list/dict/single result
        - Tries direct text fields first, then uses selector to read inner text
        """
        if result is None:
            return None

        # Normalize to a list of items to inspect
        items = []
        if isinstance(result, dict) and 'elements' in result:
            items = result.get('elements') or []
        elif isinstance(result, list):
            items = result
        else:
            items = [result]

        # First pass: use any direct text fields provided by Stagehand
        for item in items:
            text = getattr(item, 'text', None) or getattr(item, 'statusText', None)
            if isinstance(text, str) and text.strip():
                return text.strip()

        # Second pass: if a selector is available, read the element text now (avoids stale node ids)
        for item in items:
            selector = getattr(item, 'selector', None)
            if not selector:
                continue
            try:
                elem = await page.query_selector(selector)
                if elem:
                    text = await elem.inner_text()
                    if text and text.strip():
                        return text.strip()
            except Exception as e:
                logger.debug(f"extract_status_text: failed to read selector '{selector}': {e}")
                continue

        return None

    # -----------------------------
    # REPLAY MODE (NO AI)
    # -----------------------------

    async def replay_mode(self, stagehand):
        logger.info("Running REPLAY mode (no AI)")
        cached = self.load_recorded_actions()

        page = stagehand.page

        mouse = page.mouse
        keyboard = page.keyboard

        for step in cached:
            logger.debug('Start step -> %s' % step)

            t = step.get("type")

            # CLICK by coordinates
            if t == "click":
                x = step["x"]
                y = step["y"]
                button = step.get("button", "left")
                await mouse.click(x, y, button=button)

            # MOVE mouse
            elif t == "move":
                await mouse.move(step["x"], step["y"])

            # TYPE text
            elif t == "type":
                x = step["x"]
                y = step["y"]
                text = step["text"]
                await mouse.click(x, y)
                await asyncio.sleep(1)
                await keyboard.type(text)

                if step.get("press_enter_after"):
                    await keyboard.press("Enter")

            # WAIT
            elif t == "wait":
                await asyncio.sleep(step["miliseconds"] / 1000)

            # OPEN BROWSER (ignore)
            elif t == "function" and step.get("name") == "open_web_browser":
                continue

            await asyncio.sleep(5)

        await stagehand.close()
        logger.info("Replay mode completed successfully")
