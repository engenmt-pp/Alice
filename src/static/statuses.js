async function getOrderStatus() {
  const options = getOptions()
  const orderId = document.getElementById('status-order-id').value
  const statusResp = await fetch(`/api/orders-form/status/${orderId}`, {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const resp = await statusResp.json()
  addApiCalls(resp.formatted)
}

async function getSellerStatus() {
  const options = getOptions()
  const orderId = document.getElementById('status-merchant-id').value
  const statusResp = await fetch(`/api/referrals-form/status/${orderId}`, {
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

