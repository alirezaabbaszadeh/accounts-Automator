import pyotp

def test_totp_length():
    totp = pyotp.TOTP('JBSWY3DPEHPK3PXP')
    code = totp.now()
    assert len(code) == 6
