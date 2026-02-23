class CallbackClient:

    def __init__(self, http_client):
        self.http = http_client

    async def send(self, url, status, payload):
        try:
            await self.http.post(url, json={
                "status": status,
                **payload
            })
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
