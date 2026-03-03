import jwt
import sys

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ3b3Jrc3BhY2VfaWQiOiJ3cmtfMDAwVjdkTXpYSkx6UDVtWWdkZjdGempBM0oiLCJyb2xlIjoid29ya2VyX2luc3RhbmNlIiwiZXhwIjoxNzcwMDg1MzM3fQ.BkLcOMTvPW3avj9cByj-LgpGP6VFH9Rb7eg4zxK2KOs"

try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(decoded)
except Exception as e:
    print(e)
