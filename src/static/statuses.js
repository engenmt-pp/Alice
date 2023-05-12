async function getOrderStatus() {
  const options = getOptions()
  const orderId = document.getElementById('status-order-id').value
  const statusResp = await fetch(`/api/orders/status/${orderId}`, {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const resp = await statusResp.json()
  addApiCalls(resp.formatted)
}

async function getSellerStatus() {
  const options = getOptions()
  const merchantId = document.getElementById('status-merchant-id').value
  const statusResp = await fetch(`/api/partner/sellers/${merchantId}`, {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const resp = await statusResp.json()
  addApiCalls(resp.formatted)
}
async function getSellerStatusByTrackingId() {
  const options = getOptions()
  delete options['merchant-id']
  const trackingId = document.getElementById('status-tracking-id').value
  const statusResp = await fetch(`/api/partner/sellers?tracking-id=${trackingId}`, {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const resp = await statusResp.json()
  addApiCalls(resp.formatted)
}
async function getReferralStatus() {
  const options = getOptions()
  const referralToken = document.getElementById('status-referral-token').value
  const statusResp = await fetch(`/api/partner/referrals/${referralToken}`, {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const resp = await statusResp.json()
  addApiCalls(resp.formatted)
}

async function getBaStatus() {
  const options = getOptions()
  const baId = document.getElementById('status-ba-id').value
  const statusResp = await fetch(`/api/billing-form/status/${baId}`, {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const resp = await statusResp.json()
  addApiCalls(resp.formatted)
}

