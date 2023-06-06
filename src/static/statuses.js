let authHeader
async function getSellerStatus() {
  const options = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') options.authHeader = authHeader
  const merchantId = document.getElementById('status-merchant-id').value
  const statusResp = await fetch(`/api/partner/sellers/${merchantId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted } = statusData
  addApiCalls(formatted);
  ({ authHeader } = statusData)
}


async function getSellerStatusByTrackingId() {
  const options = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') options.authHeader = authHeader
  delete options['merchantId']
  const trackingId = document.getElementById('status-tracking-id').value
  const statusResp = await fetch(`/api/partner/sellers?tracking-id=${trackingId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted } = statusData
  addApiCalls(formatted);
  ({ authHeader } = statusData)
}


async function getReferralStatus() {
  const options = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') options.authHeader = authHeader
  const referralToken = document.getElementById('status-referral-token').value
  const statusResp = await fetch(`/api/partner/referrals/${referralToken}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted } = statusData
  addApiCalls(formatted);
  ({ authHeader } = statusData)
}


async function getOrderStatus() {
  const options = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') options.authHeader = authHeader
  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const orderId = document.getElementById('status-order-id').value
  const statusResp = await fetch(`/api/orders/status/${orderId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted } = statusData
  addApiCalls(formatted);
  ({ authHeader } = statusData)
}


async function getBaStatus() {
  const options = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') options.authHeader = authHeader
  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const baId = document.getElementById('status-ba-id').value
  const statusResp = await fetch(`/api/billing-form/status/${baId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted } = statusData
  addApiCalls(formatted);
  ({ authHeader } = statusData)
}


async function getPaymentTokenStatus() {
  const options = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') options.authHeader = authHeader
  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const paymentTokenId = document.getElementById('status-payment-token-id').value
  const statusResp = await fetch(`/api/vault/payment-tokenches/${paymentTokenId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted } = statusData
  addApiCalls(formatted);
  ({ authHeader } = statusData)
}


async function getPaymentTokens() {
  const options = getPartnerMerchantInfo()
  if (typeof authHeader !== 'undefined') options.authHeader = authHeader
  const id = 'include-auth-assertion'
  options[id] = document.getElementById(id).value

  const customerId = document.getElementById('status-customer-id').value
  const statusResp = await fetch(`/api/vault/customers/${customerId}`, {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const statusData = await statusResp.json()
  const { formatted } = statusData
  addApiCalls(formatted);
  ({ authHeader } = statusData)
}

