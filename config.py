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
    PARTNER_BN_CODE = os.environ.get("PARTNER_BN_CODE")
    PARTNER_ID = os.environ.get("PARTNER_ID")
    # WEBHOOK_ID = os.environ.get("WEBHOOK_ID")
    # SFTP_USERNAME = os.environ.get("SFTP_USERNAME")
    # SFTP_PASSWORD = os.environ.get("SFTP_PASSWORD")


class MerchantConfig(TestingConfig):
    # MERCHANT_CLIENT_ID = os.environ.get("MERCHANT_CLIENT_ID")
    # MERCHANT_SECRET = os.environ.get("MERCHANT_SECRET")
    MERCHANT_ID = os.environ.get("MERCHANT_ID")


class FastlanePartnerConfig(TestingConfig):
    FASTLANE_PARTNER_CLIENT_ID = os.environ.get("FASTLANE_PARTNER_CLIENT_ID")
    FASTLANE_PARTNER_SECRET = os.environ.get("FASTLANE_PARTNER_SECRET")
    FASTLANE_PARTNER_BN_CODE = os.environ.get("FASTLANE_PARTNER_BN_CODE")
    FASTLANE_PARTNER_ID = os.environ.get("FASTLANE_PARTNER_ID")


class PartnerFastlanePartnerConfig(TestingConfig):
    PARTNER_CLIENT_ID = os.environ.get("FASTLANE_PARTNER_CLIENT_ID")
    PARTNER_SECRET = os.environ.get("FASTLANE_PARTNER_SECRET")
    PARTNER_BN_CODE = os.environ.get("FASTLANE_PARTNER_BN_CODE")
    PARTNER_ID = os.environ.get("FASTLANE_PARTNER_ID")


class FastlaneMerchantConfig(TestingConfig):
    FASTLANE_MERCHANT_CLIENT_ID = os.environ.get("FASTLANE_MERCHANT_CLIENT_ID")
    FASTLANE_MERCHANT_SECRET = os.environ.get("FASTLANE_MERCHANT_SECRET")
    FASTLANE_MERCHANT_BN_CODE = os.environ.get("FASTLANE_MERCHANT_BN_CODE")
    FASTLANE_MERCHANT_ID = os.environ.get("FASTLANE_MERCHANT_ID")
