import json
import requests

from flask import Blueprint, request, current_app, jsonify

from .identity import build_headers
from .utils import (
    build_endpoint,
    format_request_and_response,
    get_managed_partner_config,
    random_decimal_string,
)


bp = Blueprint("mam", __name__, url_prefix="/mam")


class MAM:
    def __init__(self, **kwargs):
        self.partner_model = int(kwargs["partner-account-model"])
        self.auth_header = kwargs.get("authHeader") or None  # Coerce to None if empty

        self.account_id = kwargs.get("account_id")

        self.business_type = kwargs.get("business-type")

        self.legal_region_code = kwargs.get("legal-region-code")
        self.organization = kwargs.get("organization")
        self.primary_currency_code = kwargs.get("primary-currency-code")
        self.external_id = kwargs.get("external-id") or random_decimal_string(10)
        self.soft_descriptor = kwargs.get("soft-descriptor")

        self.agreement_accepted_datetime = kwargs.get("agreement-accepted-datetime")

        self.owner_given_name = kwargs.get("owner-given-name")
        self.owner_surname = kwargs.get("owner-surname")
        self.owner_citizenship = kwargs.get("owner-citizenship")
        self.owner_date_of_birth = kwargs.get("owner-date-of-birth")

        self.owner_address = self.build_address(kwargs, "owner")

        self.business_type = kwargs.get("business-type")
        self.business_name_type = kwargs.get("business-name-type")
        self.business_name = kwargs.get("business-name")
        self.business_mcc = kwargs.get("business-mcc")
        self.business_ein = kwargs.get("business-ein")
        self.business_cs_email = kwargs.get("business-cs-email")

        self.business_address = self.build_address(kwargs, "business")

        self.formatted = dict()

    def build_address(self, kwargs, prefix):
        address_line_1 = kwargs.get(f"{prefix}-address-line-1")
        address_line_2 = kwargs.get(f"{prefix}-address-line-2")

        admin_area_1 = kwargs.get(f"{prefix}-state-code")
        admin_area_2 = kwargs.get(f"{prefix}-city")

        postal_code = kwargs.get(f"{prefix}-postal-code")
        country_code = kwargs.get(f"{prefix}-country-code")

        address = {}
        if address_line_1:
            address["address_line_1"] = address_line_1
        if address_line_2:
            address["address_line_2"] = address_line_2
        if admin_area_1:
            address["admin_area_1"] = admin_area_1
        if admin_area_2:
            address["admin_area_2"] = admin_area_2
        if postal_code:
            address["postal_code"] = postal_code
        if country_code:
            address["country_code"] = country_code

        return address

    def build_headers(self):
        """Wrapper for .utils.build_headers."""

        config = get_managed_partner_config(model=self.partner_model)

        headers = build_headers(
            client_id=config["partner_client_id"],
            secret=config["partner_secret"],
            auth_header=self.auth_header,
        )

        self.formatted |= headers["formatted"]
        del headers["formatted"]

        self.auth_header = headers["Authorization"]
        return headers

    def build_individual_owner(self):
        names = [
            {
                "type": "LEGAL",
                "given_name": self.owner_given_name,
                "surname": self.owner_surname,
            }
        ]

        address = self.owner_address
        address["type"] = "HOME"
        addresses = [address]

        birth_details = {"date_of_birth": self.owner_date_of_birth}

        owner = {
            "names": names,
            "addresses": addresses,
            "birth_details": birth_details,
            "citizenship": self.owner_citizenship,
        }
        return owner

    def build_office_bearers(self):
        office_bearers = [
            {
                "names": [
                    {
                        "type": "LEGAL",
                        "given_name": self.owner_given_name,
                        "surname": self.owner_surname,
                    }
                ],
                "addresses": [{"type": "HOME", **self.owner_address}],
                "citizenship": self.owner_citizenship,
                "birth_details": {"date_of_birth": self.owner_date_of_birth},
                "identification_documents": [
                    {
                        "type": "SOCIAL_SECURITY_NUMBER",
                        "identification_number": "111223333",
                        "issuing_country_code": "US",
                    }
                ],
            }
        ]
        return office_bearers

    def build_business_entity(self):
        names = [
            {
                "type": self.business_name_type,
                "business_name": self.business_name,
            }
        ]
        address = self.business_address
        address["type"] = "BUSINESS"

        identification_documents = [
            {
                "id": "123467890ABCDEF",
                "identification_number": self.business_ein,
                "issuing_country_code": "US",
                "type": "EMPLOYER_IDENTIFICATION_NUMBER",
            },
        ]
        emails = [{"email": self.business_cs_email, "primary": "true"}]

        business_entity = {
            "type": self.business_type,
            "merchant_category_code": self.business_mcc,
            "names": names,
            "addresses": [address],
            "identification_documents": identification_documents,
            "emails": emails,
        }

        return business_entity

    def create(self):
        endpoint = build_endpoint("/v3/customer/managed-accounts")
        headers = self.build_headers()
        headers["Prefer"] = "return=representation"

        individual_owners = [self.build_individual_owner()]
        business_entity = self.build_business_entity()

        body = {
            "legal_country_code": self.legal_region_code,
            "primary_currency_code": self.primary_currency_code,
            "organization": self.organization,
            "external_id": self.external_id,
            "individual_owners": individual_owners,
            "business_entity": business_entity,
        }
        if self.soft_descriptor:
            body["soft_descriptor"] = self.soft_descriptor

        if self.agreement_accepted_datetime:
            agreements = [
                {
                    "type": "TERMS_ACCEPTED",
                    "accepted_time": f"{self.agreement_accepted_datetime}Z",
                }
            ]
            body["agreements"] = agreements

        response = requests.post(
            endpoint,
            headers=headers,
            json=body,
        )
        self.formatted["create-nlm"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }

        try:
            account_id = response.json()["account_id"]
        except Exception as exc:
            current_app.logger.error(
                f"Encountered exception unpacking account ID: {exc}"
            )
        else:
            response_dict["accountId"] = account_id
        finally:
            return response_dict

    def get_status(self):
        if self.account_id is None:
            return {"formatted": {"error": "No account ID found!"}}

        endpoint = build_endpoint(
            f"/v3/customer/managed-accounts/{self.account_id}",
            query={"views": "process_view"},
        )
        headers = self.build_headers()
        # headers["Prefer"] = "return=representation"

        response = requests.get(
            endpoint,
            headers=headers,
        )
        self.formatted["get-nlm"] = format_request_and_response(response)
        response_dict = {
            "formatted": self.formatted,
            "authHeader": self.auth_header,
        }

        return response_dict


@bp.route("/accounts", methods=("POST",))
def create_managed_account():
    data = request.get_json()
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Creating managed account with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    mam = MAM(**data)
    resp = mam.create()

    return jsonify(resp)


@bp.route("/accounts/<account_id>", methods=("POST",))
def get_managed_account(account_id):
    data = request.get_json()
    data["account_id"] = account_id
    data_filtered = {key: value for key, value in data.items() if value}
    current_app.logger.debug(
        f"Getting managed account with (filtered) data = {json.dumps(data_filtered, indent=2)}"
    )

    mam = MAM(**data)
    resp = mam.get_status()

    return jsonify(resp)
