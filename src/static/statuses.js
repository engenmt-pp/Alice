async function getOrderStatus() {
  const orderId = document.getElementById('order-id').value
  const statusResp = await fetch(`/api/orders-form/status/${orderId}`)
  const resp = await statusResp.json()
  addApiCalls(resp.formatted)
}