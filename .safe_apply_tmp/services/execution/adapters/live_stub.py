class LiveExecutionAdapterStub:
    def submit(self, intent):
        raise RuntimeError("Live adapter is gated")
