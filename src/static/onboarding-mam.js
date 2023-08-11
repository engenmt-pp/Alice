async function createReferral() {
    const options = getOptions(additionalFormId = 'mam-onboarding')
    const response = await fetch('/api/mam/', {
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
        body: JSON.stringify(options)
    })
    const createData = await response.json()
    const { formatted } = createData

    addApiCalls(formatted)
}

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
            console.log(`Model ${model} is not yet supported!`)
            eltPartnerId.value = ''
            eltPartnerClientId.value = ''
            eltPartnerBNCode.value = ''
            break
    }
}

window.addEventListener("load", setPartnerCredentials)