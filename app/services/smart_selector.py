from playwright.async_api import async_playwright
import re
import logging
from app import Config
logger = logging.getLogger(Config.APP_NAME)

# ACTIONABLE_TAGS = ["input", "button", "textarea", "select", "a", "label", "div", "span", "li", "option"]
# ACTIONABLE_ROLES = ["button", "checkbox", "radio", "link", "menuitem", "tab", "option"]

ACTIONABLE_TAGS = [
    "input", "button", "textarea", "select", "a",
    "div", "span", "li"
]

ACTIONABLE_ROLES = [
    "button", "checkbox", "radio", "link",
    "menuitem", "tab", "option", "textbox"
]

PREFERRED_DATA_ATTRS = (
    "data-testid",
    "data-test",
    "data-qa",
)

EXTJS_BAD_CLASS_PREFIXES = (
    "x-",          # ExtJS internal classes
    "x-boundlist", # dynamic
    "x-grid",      # often unstable rows
)

def is_stable_class(class_name: str) -> bool:
    if not class_name:
        return False
    return not any(class_name.startswith(p) for p in EXTJS_BAD_CLASS_PREFIXES)


async def generate_smart_selector(page, element):
    """
    ExtJS-optimized Testim-style Smart Selector generator
    """
    attrs = await page.evaluate("""
    (el) => {
        const dataAttrs = {};
        for (let a of el.attributes) {
            if (a.name.startsWith('data-')) dataAttrs[a.name] = a.value;
        }

        return {
            tag: el.tagName.toLowerCase(),
            role: el.getAttribute('role'),
            id: el.id,
            name: el.getAttribute('name'),
            placeholder: el.getAttribute('placeholder'),
            classList: [...el.classList],
            ariaLabel: el.getAttribute('aria-label'),
            ariaLabelledBy: el.getAttribute('aria-labelledby'),
            text: el.innerText?.trim() || "",
            dataAttrs: dataAttrs
        };
    }
    """, element)

    # 🔒 Filter non-actionable
    if not (
        attrs["tag"] in ACTIONABLE_TAGS
        or (attrs["role"] and attrs["role"] in ACTIONABLE_ROLES)
    ):
        return None

    # 1️⃣ data-* attributes (BEST)
    if attrs["dataAttrs"]:
        # key = list(attrs["dataAttrs"].keys())[0]
        # return f'[{key}="{attrs["dataAttrs"][key]}"]'
        for key, value in attrs["dataAttrs"].items():
            if not value:
                continue
            if key in PREFERRED_DATA_ATTRS:
                return f'[{key}="{value}"]'

    # 2️⃣ aria-label
    if attrs["ariaLabel"]:
        return f'[aria-label="{attrs["ariaLabel"]}"]'

    # 3️⃣ aria-labelledby
    if attrs["ariaLabelledBy"]:
        return f'[aria-labelledby="{attrs["ariaLabelledBy"]}"]'

    # 4️⃣ placeholder (ExtJS inputs)
    if attrs["placeholder"]:
        return f'{attrs["tag"]}[placeholder="{attrs["placeholder"]}"]'

    # 5️⃣ name attribute
    if attrs["name"]:
        return f'{attrs["tag"]}[name="{attrs["name"]}"]'

    # 6️⃣ role + visible text (ExtJS buttons, menu items)
    if attrs["role"] and attrs["text"]:
        return (
            f'xpath=//{attrs["tag"]}'
            f'[@role="{attrs["role"]}" and normalize-space()="{attrs["text"]}"]'
        )

    # 7️⃣ visible text only (common in ExtJS)
    if attrs["text"]:
        return (
            f'xpath=//{attrs["tag"]}'
            f'[normalize-space()="{attrs["text"]}"]'
        )

    # 8️⃣ stable class + tag
    stable_classes = [c for c in attrs["classList"] if is_stable_class(c)]
    if stable_classes:
        return f'{attrs["tag"]}.' + '.'.join(stable_classes[:2])
    
    # ⭐ Checkbox / radio with label (ExtJS GOLD)
    if attrs["role"] in ("checkbox", "radio") and attrs.get("labelText"):
        return (
            f'xpath=//label[normalize-space()="{attrs["labelText"]}"]'
            f'/preceding-sibling::input[@role="{attrs["role"]}"]'
        )

    # 9️⃣ LAST RESORT: id (ExtJS auto-generated)
    if attrs["id"]:
        return f'#{attrs["id"]}'

    return None


# async def generate_smart_selector(page, element_handle):
#     attrs = await page.evaluate("""
#     (el) => {
#         const dataAttrs = {};
#         for (let attr of el.attributes) {
#             if (attr.name.startsWith('data-')) dataAttrs[attr.name] = attr.value;
#         }
#         return {
#             tag: el.tagName.toLowerCase(),
#             role: el.getAttribute('role'),
#             name: el.name,
#             class: el.className,
#             ariaLabel: el.getAttribute('aria-label'),
#             ariaLabelledBy: el.getAttribute('aria-labelledby'),
#             dataAttrs: dataAttrs,
#             text: el.innerText.trim()
#         };
#     }
#     """, element_handle)

#     if not (attrs["tag"] in ACTIONABLE_TAGS or (attrs["role"] and attrs["role"] in ACTIONABLE_ROLES)):
#         return None

#     if attrs["dataAttrs"]:
#         key = list(attrs["dataAttrs"].keys())[0]
#         return f'[{key}="{attrs["dataAttrs"][key]}"]'
#     if attrs["ariaLabel"]:
#         return f'[aria-label="{attrs["ariaLabel"]}"]'
#     if attrs["ariaLabelledBy"]:
#         return f'[aria-labelledby="{attrs["ariaLabelledBy"]}"]'
#     if attrs["name"]:
#         return f'[name="{attrs["name"]}"]'
#     if attrs["class"] and attrs["text"]:
#         first_class = attrs["class"].split()[0]
#         return f'xpath=//{attrs["tag"]}[contains(@class,"{first_class}") and text()="{attrs["text"]}"]'
#     if attrs["text"]:
#         return f'xpath=//{attrs["tag"]}[text()="{attrs["text"]}"]'
#     # NEW: use placeholder for inputs or textareas
#     if attrs["tag"] in ["input", "textarea"] and await element_handle.get_attribute("placeholder"):
#         placeholder = await element_handle.get_attribute("placeholder")
#         return f'input[placeholder="{placeholder}"]'
    
#     return attrs["tag"]

# # --- Stagehand hook ---


def extract_selectors_from_message(message: str) -> list[str]:
    """
    Extract selectors from ActResult.message.
    Supports chained messages with → separator.
    """
    if not message:
        return []

    return re.findall(r"selector:\s*(xpath=[^\s→]+|css=[^\s→]+)", message)

def extract_action_value(action: dict) -> str | None:
    """
    Extract typed value from normalized action.
    """
    print("action for value extraction:", action)
    args = action.get("arguments")
    if args and isinstance(args, list):
        return args[0]
    return None

def extract_method_from_act_result(result) -> str | None:
    # 1️⃣ actions (best)
    actions = getattr(result, "actions", None)
    if actions:
        for act in actions:
            if getattr(act, "method", None):
                return act.method

    # 2️⃣ observe elements
    elements = getattr(result, "elements", None)
    if elements:
        for el in elements:
            if getattr(el, "method", None):
                return el.method

    # 3️⃣ fallback: parse message (last resort)
    message = getattr(result, "message", "")
    match = re.search(r"Action\s+\[(\w+)\]", message)
    if match:
        return match.group(1)

    return None

async def perform_act_with_smart_selector(result, page):
    smart_selectors = []
    normalized_actions = []

    # -------------------------------------------------------
    # Case A: Proper actions array exists
    # -------------------------------------------------------
    actions = getattr(result, "actions", None)
    if actions:
        for act in actions:
            selector = getattr(act, "selector", None)
            if selector:
                normalized_actions.append({
                    "selector": selector,
                    "description": getattr(act, "description", None),
                    "method": getattr(act, "method", None),
                    "arguments": getattr(act, "arguments", None),
                })

    # -------------------------------------------------------
    # Case C: ObserveResult used as action
    # -------------------------------------------------------
    raw_elements = getattr(result, "elements", None)
    if raw_elements and not normalized_actions:
        observe_list = (
            raw_elements.elements
            if hasattr(raw_elements, "elements")
            else raw_elements
            if isinstance(raw_elements, list)
            else []
        )

        for obs in observe_list:
            selector = getattr(obs, "selector", None)
            if selector:
                normalized_actions.append({
                    "selector": selector,
                    "description": getattr(obs, "description", None),
                    "method": getattr(obs, "method", None),
                    "arguments": getattr(obs, "arguments", None),
                })

    # -------------------------------------------------------
    # Case B: Parse from message (fallback)
    # -------------------------------------------------------
    if not normalized_actions:
        method = extract_method_from_act_result(result)
        message = getattr(result, "message", "")
        selectors = extract_selectors_from_message(message)

        for sel in selectors:
            normalized_actions.append({
                "selector": sel,
                "description": getattr(result, "actionDescription", None)
                               or getattr(result, "action", None),
                "method": method,
                "arguments": None,
            })

    # -------------------------------------------------------
    # Generate smart selectors
    # -------------------------------------------------------
    for action in normalized_actions:
        selector = action["selector"]
        method = action.get("method")
        value = extract_action_value(action) if method == "type" else None

        try:
            el = await page.query_selector(selector)
        except Exception:
            el = None

        if not el:
            smart_selectors.append({
                "original": selector,
                "smart": None,
                "description": action["description"],
                "method": method,
                "value": value,
                "reason": "element-not-found (likely navigation)",
            })
            continue

        try:
            smart_sel = await generate_smart_selector(page, el)
        except Exception:
            smart_sel = None

        smart_selectors.append({
            "original": selector,
            "smart": smart_sel,
            "description": action["description"],
            "method": method,
            "value": value,
        })

    return {
        "act_result": result,
        "smart_selectors": smart_selectors,
    }


# async def perform_act_with_smart_selector(result,page):
#     """
#     Execute stagehand page.act() and generate Testim-style smart selectors
#     in a safe, non-breaking way.
#     """


#     smart_selectors = []

#     # -------------------------------------------------------
#     # 1️⃣ Normalize ActResult → list of actions
#     # -------------------------------------------------------
#     normalized_actions = []

#     # Case A: Proper actions array exists
#     actions = getattr(result, "actions", None)
#     if actions:
#         for act in actions:
#             selector = getattr(act, "selector", None)
#             if selector:
#                 normalized_actions.append({
#                     "selector": selector,
#                     "description": getattr(act, "description", None),
#                     "method": getattr(act, "method", None),
#                     "arguments": getattr(act, "arguments", None),  # ✅ ADD THIS
#                 })


#     # Case C: ObserveResult used as action
#     raw_elements = getattr(result, "elements", None)
#     if raw_elements and not normalized_actions:
#         # unwrap container if needed
#         if hasattr(raw_elements, "elements"):
#             observe_list = raw_elements.elements
#         elif isinstance(raw_elements, list):
#             observe_list = raw_elements
#         else:
#             observe_list = []

#         for obs in observe_list:
#             selector = getattr(obs, "selector", None)
#             if selector:
#                 normalized_actions.append({
#                     "selector": selector,
#                     "description": getattr(obs, "description", None),
#                     "method": getattr(obs, "method", None),
#                     "arguments": getattr(obs, "arguments", None),
#                 })

#         print("case C normalized_actions", normalized_actions)

#     # Case B: No actions → parse from message
#     if not normalized_actions:
#         method = extract_method_from_act_result(result)
#         message = getattr(result, "message", "")
#         selectors = extract_selectors_from_message(message)

#         for sel in selectors:
#             normalized_actions.append({
#                 "selector": sel,
#                 "description": getattr(result, "actionDescription", None)
#                                or getattr(result, "action", None),
#                 "method": method
#             })
#     print("case B normalized_actions", normalized_actions)

#     # -------------------------------------------------------
#     # 2️⃣ Generate smart selectors (best effort)
#     # -------------------------------------------------------
#     for act in normalized_actions:
#         selector = act["selector"]
#         method = act.get("method")
#         value = extract_action_value(act) if method == "type" else None

#         try:
#             el = await page.query_selector(selector)
#         except Exception:
#             el = None

#         if not el:
#             # Element may be gone due to navigation
#             smart_selectors.append({
#                 "original": selector,
#                 "smart": None,
#                 "description": act["description"],
#                 "value": value,
#                 "reason": "element-not-found (likely navigation)",
#                 "method": method,
#             })
#             continue

#         try:
#             smart_sel = await generate_smart_selector(page, el)
#         except Exception as e:
#             smart_sel = None

#         smart_selectors.append({
#             "original": selector,
#             "smart": smart_sel,
#             "description": act["description"],
#             "value": value,
#             "method": method,
#         })

#         print(
#             f"Generated smart selector: {smart_sel} "
#             f"for action: {act['description']}"
#         )

#     # -------------------------------------------------------
#     # 3️⃣ Return enriched result (DO NOT mutate ActResult)
#     # -------------------------------------------------------

#     return {
#         "act_result": result,           # original ActResult preserved
#         "smart_selectors": smart_selectors
#     }

# async def perform_observe_with_smart_selector(page, observe_result_obj):
#     """
#     Perform observe using smart selectors instead of raw XPath.
#     Compatible with Stagehand ObserveResult container.
#     """
#     print("perform_observe_with_smart_selector called with:", observe_result_obj)
#     if not observe_result_obj or not getattr(observe_result_obj, "elements", None):
#         logger.warning("⚠️ Observe result has no elements")
#         return observe_result_obj

#     new_elements = []

#     for observe in observe_result_obj.elements:
#         raw_selector = observe.selector
#         description = observe.description
#         method = observe.method
#         arguments = observe.arguments or []

#         # 1️⃣ Resolve DOM element
#         try:
#             selector = raw_selector.replace("xpath=", "")
#             element = await page.query_selector(selector)
#         except Exception:
#             element = None

#         if not element:
#             logger.warning(f"⚠️ Observe element not found: {raw_selector}")
#             new_elements.append(observe)
#             continue

#         # 2️⃣ Generate smart selector
#         smart_selector = await generate_smart_selector(page, element)

#         if not smart_selector or is_bad_selector(smart_selector):
#             logger.warning(
#                 f"⚠️ Smart selector rejected for observe: {description}"
#             )
#             new_elements.append(observe)
#             continue

#         logger.info(
#             f"🔍 Smart observe selector generated: {smart_selector} "
#             f"for description: {description}"
#         )

#         # 3️⃣ Replay observe with smart selector
#         try:
#             smart_instruction = {
#                 "selector": smart_selector,
#                 "description": description,
#                 "method": method,
#                 "arguments": arguments,
#             }

#             smart_result = await page.observe(smart_instruction)

#             # stagehand.observe returns the SAME container shape
#             if smart_result and getattr(smart_result, "elements", None):
#                 new_elements.extend(smart_result.elements)
#             else:
#                 new_elements.append(observe)

#         except Exception as e:
#             logger.warning(
#                 f"⚠️ Smart observe failed, fallback to raw selector. Error: {e}"
#             )
#             new_elements.append(observe)
        
#     print("perform_observe_with_smart_selector new_elements", smart_instruction)

#     return smart_instruction

async def perform_observe_with_smart_selector(page, observe_results):
    """
    Perform observe using smart selectors instead of raw XPath.
    observe_results: List[ObserveResult]
    """

    logger.debug(
        f"perform_observe_with_smart_selector called with: {observe_results}"
    )

    if not observe_results or not isinstance(observe_results, list):
        logger.warning("⚠️ Observe result is empty or invalid")
        return observe_results

    new_results = []

    for observe in observe_results:
        raw_selector = observe.selector
        description = observe.description
        method = observe.method
        arguments = observe.arguments or []

        # ---------------------------------------------------
        # 1️⃣ Resolve DOM element (CSS vs XPath)
        # ---------------------------------------------------
        try:
            if raw_selector.startswith("xpath="):
                element = await page.locator(raw_selector).element_handle()
            else:
                element = await page.query_selector(raw_selector)
        except Exception:
            element = None

        if not element:
            logger.warning(f"⚠️ Observe element not found: {raw_selector}")
            new_results.append(observe)
            continue

        # ---------------------------------------------------
        # 2️⃣ Generate smart selector
        # ---------------------------------------------------
        try:
            smart_selector = await generate_smart_selector(page, element)
        except Exception as e:
            logger.warning(f"⚠️ Smart selector generation failed: {e}")
            smart_selector = None

        if not smart_selector or is_bad_selector(smart_selector):
            logger.warning(
                f"⚠️ Smart selector rejected for observe: {description}"
            )
            new_results.append(observe)
            continue

        logger.info(
            f"🔍 Smart observe selector generated: {smart_selector} "
            f"for description: {description}"
        )
    return smart_selector


def is_bad_selector(selector: str) -> bool:
    return (
        selector.startswith("#ext-gen")
        or 'data-errorqtip' in selector
        or selector.endswith('=""')
    )

def normalize_selector_used(value):
    # Case 1: string → OK
    if isinstance(value, str):
        return value

    # Case 2: ObserveResult → extract selector
    if hasattr(value, "selector"):
        return value.selector

    # Case 3: list → normalize each item
    if isinstance(value, list):
        return [normalize_selector_used(v) for v in value]

    # Case 4: dict → normalize values
    if isinstance(value, dict):
        return {
            k: normalize_selector_used(v)
            for k, v in value.items()
        }

    # Case 5: unknown / unsafe
    return None



