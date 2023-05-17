function populateReferralLink(actionUrl) {
  const anchor = document.getElementById('anchor-referral')
  anchor.href = `${actionUrl}&displayMode=minibrowser`
  anchor.classList.remove('hidden')
}
function hideGenerateButton() {
  const generateButton = document.getElementById('button-generate')
  generateButton.classList.add('hidden')
}
async function generateReferralLink() {
  const options = getOptions()
  const response = await fetch('/api/partner/referrals', {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const responseJson = await response.json()

  updateAPICalls(responseJson.formatted)
  if (responseJson.hasOwnProperty('actionUrl')) {
    const actionUrl = responseJson.actionUrl
    hideGenerateButton()
    populateReferralLink(actionUrl)
  }
}