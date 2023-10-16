async function getSellerStatus() {
  const options = getPartnerMerchantInfo()

  const merchantId = document.getElementById('status-merchant-id').value
  options['merchant-id'] = merchantId

  const statusResp = await fetch(`/api/partner/sellers/${merchantId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted, authHeader } = statusData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}


async function getSellerStatusByTrackingId() {
  const options = getPartnerMerchantInfo()

  delete options['merchant-id']

  const trackingId = document.getElementById('status-tracking-id').value
  const statusResp = await fetch(`/api/partner/sellers?tracking-id=${trackingId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted, authHeader } = statusData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}


async function getReferralStatus() {
  const options = getPartnerMerchantInfo()

  const referralToken = document.getElementById('status-referral-token').value
  const statusResp = await fetch(`/api/partner/referrals/${referralToken}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted, authHeader } = statusData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}


async function getOrderStatus() {
  const options = getPartnerMerchantInfo()
  console.log("Options", options)

  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const orderId = document.getElementById('status-order-id').value
  if (!orderId) {
    return
  }
  const statusResp = await fetch(`/api/orders/${orderId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted, authHeader } = statusData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}


async function getBaStatus() {
  const options = getPartnerMerchantInfo()

  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const baId = document.getElementById('status-ba-id').value
  const statusResp = await fetch(`/api/billing-form/status/${baId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted, authHeader } = statusData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}


async function deletePaymentToken() {
  const options = getPartnerMerchantInfo()

  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const paymentTokenId = document.getElementById('status-payment-token-id').value
  const deleteResp = await fetch(`/api/vault/payment-tokens/${paymentTokenId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'DELETE',
    body: JSON.stringify(options)
  })
  const deleteData = await deleteResp.json()
  const { formatted, authHeader } = deleteData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}


async function getPaymentTokenStatus() {
  const options = getPartnerMerchantInfo()

  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const paymentTokenId = document.getElementById('status-payment-token-id').value
  const statusResp = await fetch(`/api/vault/payment-tokens/${paymentTokenId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted, authHeader } = statusData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}


async function getPaymentTokens() {
  const options = getPartnerMerchantInfo()

  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const customerId = document.getElementById('status-customer-id').value
  const statusResp = await fetch(`/api/vault/customers/${customerId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted, authHeader } = statusData
  setAuthHeader(authHeader)
  addApiCalls(formatted)
}

