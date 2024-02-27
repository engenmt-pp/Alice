import {
  addApiCalls,
  getOptions,
  setAuthHeader
} from './utils.js'


function populateReferralLink(actionUrl, onboardCompleteCallback) {
  const anchor = document.getElementById('partner-referral')
  anchor.href = `${actionUrl}&displayMode=minibrowser`

  if (onboardCompleteCallback) {
    anchor.setAttribute('data-paypal-onboard-complete', onboardCompleteCallback)
  }

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

let sellerNonce
async function createReferral() {
  const options = getOptions()
  const response = await fetch('/api/partner/referrals', {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const createData = await response.json()
  const { formatted, actionUrl, authHeader } = createData;
  ({ sellerNonce } = createData)
  setAuthHeader(authHeader)

  if (actionUrl) {
    addApiCalls(formatted, false)
    const onboardCompleteCallback_ = (
      options.party === 'first' ? getSellerAccessToken : false
    )
    window.onboardCompleteCallback = onboardCompleteCallback_
    populateReferralLink(actionUrl, 'onboardCompleteCallback')
  } else {
    console.error('No actionUrl found:', createData)
    addApiCalls(formatted)
  }
}

async function getSellerAccessToken(authCode, sharedId) {
  const response = await fetch('/api/identity/seller-access-token', {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify({
      'auth-code': authCode,
      'shared-id': sharedId,
      'seller-nonce': sellerNonce
    })
  })
  const { formatted, access_token: accessToken } = await response.json()
  addApiCalls(formatted)
  // alert(`Onboarding complete!\nauthCode: ${authCode}\nsharedId: ${sharedId}`)

  getSellerCredentials(accessToken)
}

async function getSellerCredentials(accessToken) {
  const partnerId = document.getElementById('partner-id').value

  const response = await fetch('/api/identity/seller-credentials', {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify({
      'partner-id': partnerId,
      'access-token': accessToken,
    })
  })
  const { formatted } = await response.json()
  addApiCalls(formatted)
}

// async function createFirstPartyURL() {
//   const endpoint = "https://www.paypal.com/bizsignup/partner/entry"
//   const url = new URL(endpoint)
//   const query = url.searchParams
//   const options = getOptions()
//   query.set('partnerId', partnerId)
//   let partnerId = ""
//   let product = "EXPRESS_CHECKOUT"
//   let integrationType = "FO"
//   let partnerClientId = ""
//   // let returnToPartnerUrl = "google.com"
//   // let partnerLogoUrl = ""
//   let displayMode = "minibrowser"
//   let sellerNonce = "1234567890123456789012345678901234567890"
//   let features = ["PAYMENT", "REFUND"]
// }

export {
  createReferral as default
}
