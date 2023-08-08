async function createReferral() {
    const options = getOptions()
    const response = await fetch('/api/mam/referrals', {
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
        body: JSON.stringify(options)
    })
    const createData = await response.json()
    const { formatted } = createData

    addApiCalls(formatted)
}