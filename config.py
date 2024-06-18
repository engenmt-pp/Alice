import flask
import os

flask.cli.load_dotenv()


class SandboxConfig:
    ENV = "development"
    ENDPOINT_PREFIX = "https://api-m.sandbox.paypal.com"

    SFTP_HOSTNAME = "reports.sandbox.paypal.com"


class TestingConfig(SandboxConfig):
    DEBUG = False


class PartnerConfig(TestingConfig):
    PARTNER_CLIENT_ID = os.environ.get("PARTNER_CLIENT_ID")
    PARTNER_SECRET = os.environ.get("PARTNER_SECRET")
    PARTNER_ID = os.environ.get("PARTNER_ID")
    PARTNER_BN_CODE = os.environ.get("PARTNER_BN_CODE")

    WEBHOOK_ID = os.environ.get("WEBHOOK_ID")

    SFTP_USERNAME = os.environ.get("SFTP_USERNAME")
    SFTP_PASSWORD = os.environ.get("SFTP_PASSWORD")


class MerchantConfig(TestingConfig):
    MERCHANT_CLIENT_ID = os.environ.get("MERCHANT_CLIENT_ID")
    MERCHANT_SECRET = os.environ.get("MERCHANT_SECRET")
    MERCHANT_ID = os.environ.get("MERCHANT_ID")


class FastlaneConfig(TestingConfig):
    FASTLANE_CLIENT_ID = os.environ.get("FASTLANE_CLIENT_ID")
    FASTLANE_BN_CODE = os.environ.get("FASTLANE_BN_CODE")
    FASTLANE_SECRET = os.environ.get("FASTLANE_SECRET")
    FASTLANE_ID = os.environ.get("FASTLANE_ID")
