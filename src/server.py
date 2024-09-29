import asyncio
import logging
import os
import uvicorn
from fastapi import FastAPI
from starlette.requests import Request

from sse_starlette.sse import EventSourceResponse
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import yaml
from fastapi.templating import Jinja2Templates
from constants import F_SWITCH

_log = logging.getLogger(__name__)
log_fmt = r"%(asctime)-15s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=log_fmt, level=logging.DEBUG, datefmt=datefmt)

app = FastAPI()


# YAML file path
yaml_file_path = "../data/settings.yml"

# Serve static files (CSS, JavaScript, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")
messages = []


class Message(BaseModel):
    content: str


@app.get("/log")
async def show_log(req: Request):
    """Simulates and endless stream

    In case of server shutdown the running task has to be stopped via signal handler in order
    to enable proper server shutdown. Otherwise, there will be dangling tasks preventing proper shutdown.
    """

    async def event_publisher():

        try:
            while True:
                # yield dict(id=..., event=..., data=...)
                if any(messages):
                    yield messages
                    messages.pop(0)
                else:
                    await asyncio.sleep(0.9)
        except asyncio.CancelledError as e:
            _log.info(f"Disconnected from client (via refresh/close) {req.client}")
            # Do any other cleanup, if any
            raise e

    return EventSourceResponse(event_publisher())


# Read YAML file
def read_yaml_file():
    if os.path.exists(yaml_file_path):
        with open(yaml_file_path, "r") as file:
            return yaml.safe_load(file)
    return {}


# Write to YAML file
def write_yaml_file(data):
    with open(yaml_file_path, "w") as file:
        yaml.dump(data, file)


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    # Read the YAML file
    yaml_data = read_yaml_file()

    # Render the Jinja template
    return templates.TemplateResponse(
        "home.html", {"request": request, "yaml_data": yaml_data}
    )


@app.post("/update_yaml")
async def update_yaml(update_data: dict):
    try:
        # Read the current YAML data
        current_data = read_yaml_file()

        # Modify this part to include new keys in the YAML file
        for key, value in update_data.items():
            current_data[key] = value  # This will add new keys or update existing ones

        # Write the updated data to the YAML file
        write_yaml_file(current_data)

        return JSONResponse(
            content={"message": "YAML file updated successfully"}, status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Error updating YAML file: {str(e)}"}, status_code=500
        )


@app.get("/show", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/enable")
async def enable_toggle(request: Request):
    """save settings"""
    data = await request.json()
    toggle_value = data.get("toggleValue")

    try:
        # Write the value to switch.txt
        with open(F_SWITCH, "w") as file:
            file.write(str(toggle_value))
        return JSONResponse(content={"message": f"Value saved: {toggle_value}"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/send_message")
async def send_message(message: Message):
    # Extract message content
    message_content = message.content

    # Add the message to the in-memory store
    messages.append(message_content)

    # Return a JSON response confirming receipt of the message
    return JSONResponse(content={"status": "Message received"}, status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="trace", log_config=None)  # type: ignore
