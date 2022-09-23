import flask
import os

flask.cli.load_dotenv()


class Config(object):
    pass


class SandboxConfig(Config):
    ENV = "development"
    ENDPOINT_PREFIX = "https://api-m.sandbox.paypal.com"

    SFTP_HOSTNAME = "reports.sandbox.paypal.com"


class ProductionConfig(Config):
    ENV = "production"
    ENDPOINT_PREFIX = "https://api-m.paypal.com"

    SFTP_HOSTNAME = "reports.paypal.com"


class TestingConfig(SandboxConfig):
    DEBUG = True


class PartnerOneConfig(TestingConfig):
    PARTNER_CLIENT_ID = os.environ.get("PARTNER_CLIENT_ID")
    PARTNER_SECRET = os.environ.get("PARTNER_SECRET")
    PARTNER_ID = os.environ.get("PARTNER_ID")
    PARNTER_ACCOUNT_NUM = os.environ.get("PARNTER_ACCOUNT_NUM")
    PARTNER_BN_CODE = os.environ.get("PARTNER_BN_CODE")

    WEBHOOK_ID = os.environ.get("WEBHOOK_ID")

    SFTP_USERNAME = os.environ.get("SFTP_USERNAME")
    SFTP_PASSWORD = os.environ.get("SFTP_PASSWORD")


class MerchantOneConfig(TestingConfig):
    MERCHANT_CLIENT_ID = os.environ.get("MERCHANT_CLIENT_ID")
    MERCHANT_SECRET = os.environ.get("MERCHANT_SECRET")
    MERCHANT_ID = os.environ.get("MERCHANT_ID")


class MerchantPPGFConfig(TestingConfig):
    MERCHANT_ID = os.environ.get("MERCHANT_PPGF_ID")
