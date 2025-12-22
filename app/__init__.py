import asyncio
import logging

import click
from flask import Flask
from flask.cli import with_appcontext

from app.config import Config

from app.resources import api, initLogger

logger = logging.getLogger(Config.APP_NAME)


def create_app() -> Flask:
    app = Flask(__name__)

    api.api.init_app(app)

    @click.command()
    @click.option("--mode", default="ai", help="ai or replay")
    @with_appcontext
    def process(mode):
        initLogger()
        from app.services.main import MainService
        asyncio.run(MainService().process(mode=mode))


    @click.command()
    @click.option("--input", default="./storage/steps.txt", help="Input steps file path")
    @click.option("--output-json", default="./storage/actions.json", help="Output JSON file path")
    @click.option("--output-text", default="./storage/actions_natural.txt", help="Output natural language file path")
    @with_appcontext
    def convert_steps(input, output_json, output_text):
        """Convert human-written test steps to Stagehand-friendly actions."""
        initLogger()
        from app.utils.step_converter import convert_steps_to_actions
        
        logger.info(f"Converting steps from: {input}")
        actions = convert_steps_to_actions(input, output_json, output_text)
        logger.info(f"✓ Converted {len(actions)} actions")
        logger.info(f"✓ JSON output: {output_json}")
        logger.info(f"✓ Text output: {output_text}")

    app.cli.add_command(process)
    app.cli.add_command(convert_steps)

    logger.info("Version -> %s" % Config.VERSION)
    return app
