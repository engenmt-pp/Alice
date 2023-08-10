async function createReferral() {
    const options = getOptions(additionalFormId = 'mam-onboarding')
    const response = await fetch('/api/mam/', {
        headers: { 'Content-Type': 'application/json' },
        method: 'POST',
        body: JSON.stringify(options)
    })
    const createData = await response.json()
    const { formatted } = createData

    addApiCalls(formatted)
}