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
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify(options)
  })
  const createData = await response.json()
  const { formatted, actionUrl } = createData

  if (actionUrl == null) {
    console.error('No actionUrl found:', createData)
    addApiCalls(formatted, click = true)
  } else {
    addApiCalls(formatted, click = false)
    hideCreateReferral()
    populateReferralLink(actionUrl)
  }
}