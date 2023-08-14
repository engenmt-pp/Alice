function setPartnerCredentials() {
    const model = document.getElementById('partner-account-model').value

    const eltPartnerId = document.getElementById('partner-id')
    const eltPartnerClientId = document.getElementById('partner-client-id')
    const eltPartnerBNCode = document.getElementById('partner-bn-code')
    switch (model) {
        case "1":
            eltPartnerId.value = '9P94JRPRJ8QYL'
            eltPartnerClientId.value = 'AfskEKI9yB2g2aBYYLFPLvDGy5TYNYPx3ZMjXf28V4aLrRCBtBhz05wT6YOOMDudZAgIQgDb3cJuVN3q'
            eltPartnerBNCode.value = 'gms_mgd_mod1'
            break
        default:
            alert(`Model ${model} is not yet supported!`)
            eltPartnerId.value = ''
            eltPartnerClientId.value = ''
            eltPartnerBNCode.value = ''
            break
    }
}

function updateManagedAccount(accountId = null) {
    const eltAccountId = document.getElementById('managed-account-id')
    if (accountId != null) {
        eltAccountId.value = accountId
    } else {
        accountId = eltAccountId.value
    }

    if (accountId != null) {
        document.getElementById('managed-account-button').disabled = false
    } else {
        document.getElementById('managed-account-button').disabled = true
    }
}

async function createReferral() {
    const options = getOptions(additionalFormId = 'mam-onboarding')
    const response = await fetch('/api/mam/accounts', {
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
        body: JSON.stringify(options)
    })
    document.body.style.cursor = 'wait !important'
    const createData = await response.json()
    const { formatted, accountId } = createData
    document.body.style.cursor = 'default'

    addApiCalls(formatted)
    updateManagedAccount(accountId)
}

async function getManagedAccount() {
    const accountId = document.getElementById('managed-account-id').value
    const options = getOptions()
    const response = await fetch(`/api/mam/accounts/${accountId}`, {
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
        body: JSON.stringify(options)
    })
    const getData = await response.json()
    const { formatted } = getData

    addApiCalls(formatted)
}



window.addEventListener("load", setPartnerCredentials)