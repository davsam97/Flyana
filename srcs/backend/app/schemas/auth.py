from pydantic import BaseModel

class TwoFASetupResponse(BaseModel):
    otpauth_uri: str
    qr_code_png_base64: str

class TwoFAEnableRequest(BaseModel):
    code: str

class TwoFAEnableResponse(BaseModel):
    backup_codes: list[str]

class TwoFAVerifyRequest(BaseModel):
    code: str

class TwoFADisableRequest(BaseModel):
    password: str
    code: str