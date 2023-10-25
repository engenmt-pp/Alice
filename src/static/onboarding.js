import {
  addApiCalls,
  getOptions,
  setAuthHeader
} from './utils.js'

function populateReferralLink(actionUrl) {
  const anchor = document.getElementById('partner-referral')
  anchor.href = `${actionUrl}&displayMode=minibrowser`


  if (anchor.getAttribute('style')) {
    anchor.setAttribute('style', '')
  } else {
    addProxyReferral()
  }

}

function addProxyReferral() {
  const proxyAnchor = document.createElement('a')
  proxyAnchor.className = 'proxy'
  proxyAnchor.innerHTML = 'Begin onboarding'

  const div = document.querySelector('[data-page=onboarding]')
  div.prepend(proxyAnchor)
}


async function createReferral() {
  const options = getOptions()
  const response = await fetch('/api/partner/referrals', {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const createData = await response.json()
  const { formatted, actionUrl, authHeader } = createData
  setAuthHeader(authHeader)

  if (actionUrl == null) {
    console.error('No actionUrl found:', createData)
    addApiCalls(formatted)
  } else {
    addApiCalls(formatted, false)
    populateReferralLink(actionUrl)
  }
}

async function createFirstPartyURL() {
  const endpoint = "https://www.paypal.com/bizsignup/partner/entry"
  const url = new URL(endpoint)
  const query = url.searchParams
  const options = getOptions()
  query.set('partnerId', partnerId)
  let partnerId = ""
  let product = "EXPRESS_CHECKOUT"
  let integrationType = "FO"
  let partnerClientId = ""
  // let returnToPartnerUrl = "google.com"
  // let partnerLogoUrl = ""
  let displayMode = "minibrowser"
  let sellerNonce = "1234567890123456789012345678901234567890"
  let features = ["PAYMENT", "REFUND"]
}

export {
  createReferral as default
}