"""HTTP-safe errors shared by isolated synthetic business domains."""
class DemoError(Exception):
    def __init__(self,status,message): self.status,self.message=status,message
