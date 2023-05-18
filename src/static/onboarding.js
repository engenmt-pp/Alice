function populateReferralLink(actionUrl) {
  const anchor = document.getElementById('partner-referral')
  anchor.href = `${actionUrl}&displayMode=minibrowser`
  anchor.classList.remove('hidden')
}


function hideCreateReferral() {
  const generateButton = document.getElementById('create-referral')
  generateButton.classList.add('hidden')
}


async function createReferral() {
  const options = getOptions()
  const response = await fetch('/api/partner/referrals', {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const createData = await response.json()
  const { formatted, actionUrl } = createData

  addApiCalls(formatted)
  if (typeof actionUrl !== 'undefined') {
    hideCreateReferral()
    populateReferralLink(actionUrl)
  } else {
    console.error('No actionUrl found:', createData)
  }
}


async function getSellerStatus() {
  const options = getPartnerMerchantInfo()
  const merchantId = document.getElementById('status-merchant-id').value
  const statusResp = await fetch(`/api/partner/sellers/${merchantId}`, {
    headers: {'Content-Type': 'application/json'},
    method: 'POST',
    body: JSON.stringify(options)
  })
  const { formatted } = await statusResp.json()
  addApiCalls(formatted)
}

