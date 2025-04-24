import httpx
import asyncio
import yaml


class LuxulPdu:
    """Interface for controlling Luxul PDU devices over HTTP"""

    @classmethod
    def from_yaml(cls, config_file):
        """Create a LuxulPdu instance from a YAML configuration."""
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        host = config.get("host")
        username = config.get("username")
        password = config.get("password")
        return cls(host, username, password)

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def write_config(self, config_file):
        """Write the configuration to a YAML file."""
        config = {
            "host": self.host,
            "username": self.username,
            "password": self.password,
        }
        with open(config_file, "w") as file:
            yaml.dump(config, file)

    async def _submit(self, data):
        url = f"http://{self.host}/outletsubmit.htm"
        auth = (self.username, self.password)
        try:
            async with httpx.AsyncClient(auth=auth, verify=False, http2=False) as client:
                response = await client.post(url, data=data)
                return response.status_code, response.text
        except httpx.RemoteProtocolError:
            # There is a bug in the Luxul firmware that causes it to return a
            # malformed HTTP response.  It sends an HTTP response that starts
            # like this (2nd line is gross):
            #
            #   HTTP/1.1 200 OK
            #   ConnectiHTTP/1.1 200 OK
            #   Connection: close
            #
            # And this will cause sane parsers to throw an error.  We can
            # ignore this error and pretend everything is OK...
            return 200, "OK"

    async def set(self, outlet, on):
        data = {"controlnum": outlet, "command": "ON" if on else "OFF", "delay": "0"}
        status, response_text = await self._submit(data)
        return status, response_text

    async def cycle(self, outlet, delay):
        data = {"controlnum": outlet, "command": "CYCLE", "delay": str(delay)}
        status, response_text = await self._submit(data)
        return status, response_text
