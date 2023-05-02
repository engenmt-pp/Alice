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

