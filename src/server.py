from constants import F_SWITCH, F_SETG, O_SETG, O_FUTL, logging
import asyncio
import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
import yaml

from sse_starlette.sse import EventSourceResponse
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")
messages = []


class Message(BaseModel):
    content: str


@app.post("/send_message")
async def send_message(message: Message):
    # Extract message content
    message_content = message.content

    # Add the message to the in-memory store
    messages.append(message_content)

    # Return a JSON response confirming receipt of the message
    return JSONResponse(content={"status": "Message received"}, status_code=200)


@app.get("/show", response_class=HTMLResponse)
async def show_message(request: Request):
    return templates.TemplateResponse("show.html", {"request": request})


@app.get("/log")
async def show_log(req: Request):
    """Simulates an endless stream
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
            logging.debug(f"disconnected from client (via refresh/close) {req.client}")
            # Do any other cleanup, if any
            raise e

    return EventSourceResponse(event_publisher())


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    # Render the Jinja template
    return templates.TemplateResponse(
        "home.html", {"request": request, "yaml_data": O_SETG}
    )


@app.post("/update_yaml")
async def update_yaml(update_data: dict):
    try:
        # Modify this part to include new keys in the YAML file
        for key, value in update_data.items():
            O_SETG[key] = value  # This will add new keys or update existing ones

        with open(F_SETG, "w") as file:
            yaml.dump(O_SETG, file)

            return JSONResponse(
                content={"message": "YAML file updated successfully"}, status_code=200
            )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Error updating YAML file: {str(e)}"}, status_code=500
        )


@app.post("/enable")
async def enable_toggle(request: Request):
    """enable_trades"""
    data = await request.json()
    toggle_value = data.get("toggleValue")

    try:
        # Write the value to switch.txt
        with open(F_SWITCH, "w") as file:
            file.write(str(toggle_value))
        return JSONResponse(content={"message": f"Value saved: {toggle_value}"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="trace", log_config=None)  # type: ignore
