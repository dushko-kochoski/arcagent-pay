import { useEffect, useState } from 'react'
import './App.css'

const ARC_EXPLORER = 'https://explorer.testnet.arc.io'

function shortAddress(address) {
  if (!address) return '—'
  return `${address.slice(0, 6)}...${address.slice(-4)}`
}

function formatUsdc(value) {
  if (value === null || value === undefined) return '—'

  const number = Number(value)

  if (Number.isNaN(number)) return value

  return `${number.toLocaleString(undefined, {
    maximumFractionDigits: 6,
  })} USDC`
}

function formatTime(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString()
}

async function readJson(response) {
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      data?.detail ||
      `Request failed with HTTP ${response.status}`

    throw new Error(message)
  }

  return data
}

function App() {
  const [vault, setVault] = useState(null)
  const [history, setHistory] = useState([])

  const [recipient, setRecipient] = useState('')
  const [amount, setAmount] = useState('1')

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const [loadError, setLoadError] = useState('')
  const [paymentResult, setPaymentResult] = useState(null)

  async function loadVault() {
    const response = await fetch('/api/vault/status')
    const data = await readJson(response)

    setVault(data)

    setRecipient((currentRecipient) => {
      if (currentRecipient) {
        return currentRecipient
      }

      return data.owner || ''
    })
  }

  async function loadHistory() {
    const response = await fetch(
      '/api/payments/history?limit=20',
    )

    const data = await readJson(response)

    setHistory(data)
  }

  async function refreshDashboard() {
    setLoading(true)
    setLoadError('')

    try {
      await Promise.all([
        loadVault(),
        loadHistory(),
      ])
    } catch (error) {
      setLoadError(error.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshDashboard()
  }, [])

  async function handlePayment(event) {
    event.preventDefault()

    setSubmitting(true)
    setPaymentResult(null)

    try {
      const response = await fetch(
        '/api/payments/execute',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            recipient,
            amount_usdc: amount,
          }),
        },
      )

      const data = await readJson(response)

      setPaymentResult({
        type: 'approved',
        message: `${amount} USDC payment approved`,
        txHash: data.tx_hash,
        explorerUrl: data.explorer_url,
      })

      await Promise.all([
        loadVault(),
        loadHistory(),
      ])
    } catch (error) {
      setPaymentResult({
        type: 'rejected',
        message: error.message,
      })

      try {
        await loadHistory()
      } catch {
        // Keep the original payment error visible.
      }
    } finally {
      setSubmitting(false)
    }
  }

  const vaultActive = vault && !vault.paused

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <div className="brand-row">
            <div className="brand-mark">A</div>

            <div>
              <h1>ArcAgent Pay</h1>
              <p className="subtitle">
                On-chain spending controls for autonomous agents
              </p>
            </div>
          </div>
        </div>

        <div className="network-area">
          <span className="network-dot" />
          Arc Testnet
        </div>
      </header>

      {loadError && (
        <section className="alert alert-error">
          <strong>Backend unavailable</strong>
          <span>{loadError}</span>
        </section>
      )}

      <section className="hero-panel">
        <div>
          <p className="eyebrow">
            PROGRAMMABLE AGENT TREASURY
          </p>

          <h2>
            The AI requests payments.
            <br />
            The smart contract decides.
          </h2>

          <p className="hero-copy">
            ArcAgent Pay lets an autonomous agent spend USDC
            while the vault enforces recipient, transaction,
            daily, expiry and emergency controls on-chain.
          </p>
        </div>

        <div
          className={
            vaultActive
              ? 'status-pill status-active'
              : 'status-pill status-paused'
          }
        >
          <span className="status-dot" />

          {loading
            ? 'Loading'
            : vaultActive
              ? 'Vault active'
              : 'Vault paused'}
        </div>
      </section>

      <section className="stats-grid">
        <article className="stat-card">
          <span>Vault balance</span>
          <strong>
            {formatUsdc(vault?.balance_usdc)}
          </strong>
          <small>Available agent treasury</small>
        </article>

        <article className="stat-card">
          <span>Per-payment limit</span>
          <strong>
            {formatUsdc(
              vault?.per_transaction_limit_usdc,
            )}
          </strong>
          <small>Maximum single transaction</small>
        </article>

        <article className="stat-card">
          <span>Spent today</span>
          <strong>
            {formatUsdc(vault?.spent_today_usdc)}
          </strong>
          <small>
            Daily limit:{' '}
            {formatUsdc(vault?.daily_limit_usdc)}
          </small>
        </article>

        <article className="stat-card">
          <span>Remaining today</span>
          <strong>
            {formatUsdc(
              vault?.remaining_today_usdc,
            )}
          </strong>
          <small>Available under daily policy</small>
        </article>
      </section>

      <section className="main-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                AGENT ACTION
              </p>
              <h3>Request payment</h3>
            </div>
          </div>

          <form
            className="payment-form"
            onSubmit={handlePayment}
          >
            <label>
              Recipient
              <input
                type="text"
                value={recipient}
                onChange={(event) =>
                  setRecipient(event.target.value)
                }
                placeholder="0x..."
                required
              />
            </label>

            <label>
              Amount
              <div className="amount-input">
                <input
                  type="number"
                  min="0.000001"
                  step="0.000001"
                  value={amount}
                  onChange={(event) =>
                    setAmount(event.target.value)
                  }
                  required
                />
                <span>USDC</span>
              </div>
            </label>

            <button
              className="primary-button"
              type="submit"
              disabled={submitting}
            >
              {submitting
                ? 'Submitting to Arc...'
                : 'Request payment'}
            </button>
          </form>

          {paymentResult && (
            <div
              className={
                paymentResult.type === 'approved'
                  ? 'payment-result result-approved'
                  : 'payment-result result-rejected'
              }
            >
              <strong>
                {paymentResult.type === 'approved'
                  ? 'Approved'
                  : 'Rejected'}
              </strong>

              <span>{paymentResult.message}</span>

              {paymentResult.explorerUrl && (
                <a
                  href={paymentResult.explorerUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  View transaction on Arc Explorer ↗
                </a>
              )}
            </div>
          )}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                ON-CHAIN POLICY
              </p>
              <h3>Vault controls</h3>
            </div>
          </div>

          <dl className="policy-list">
            <div>
              <dt>Status</dt>
              <dd>
                {vault?.paused
                  ? 'Paused'
                  : 'Active'}
              </dd>
            </div>

            <div>
              <dt>Allowlist</dt>
              <dd>
                {vault?.allowlist_enabled
                  ? 'Enabled'
                  : 'Disabled'}
              </dd>
            </div>

            <div>
              <dt>Owner</dt>
              <dd title={vault?.owner}>
                {shortAddress(vault?.owner)}
              </dd>
            </div>

            <div>
              <dt>Authorised Agent</dt>
              <dd title={vault?.agent}>
                {shortAddress(vault?.agent)}
              </dd>
            </div>

            <div>
              <dt>Policy expiry</dt>
              <dd>
                {vault?.policy_expires_at === 0
                  ? 'No expiry'
                  : vault?.policy_expires_at || '—'}
              </dd>
            </div>
          </dl>

          {vault?.vault_address && (
            <a
              className="secondary-link"
              href={`${ARC_EXPLORER}/address/${vault.vault_address}`}
              target="_blank"
              rel="noreferrer"
            >
              View vault on Arc Explorer ↗
            </a>
          )}
        </article>
      </section>

      <section className="panel activity-panel">
        <div className="panel-heading activity-heading">
          <div>
            <p className="eyebrow">
              AUDIT TRAIL
            </p>
            <h3>Payment activity</h3>
          </div>

          <button
            type="button"
            className="refresh-button"
            onClick={refreshDashboard}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {history.length === 0 ? (
          <div className="empty-state">
            No payment activity yet.
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Amount</th>
                  <th>Recipient</th>
                  <th>Time</th>
                  <th>Transaction</th>
                </tr>
              </thead>

              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span
                        className={
                          item.status === 'approved'
                            ? 'activity-status approved'
                            : 'activity-status rejected'
                        }
                      >
                        {item.status}
                      </span>
                    </td>

                    <td>
                      {formatUsdc(item.amount_usdc)}
                    </td>

                    <td title={item.recipient}>
                      {shortAddress(item.recipient)}
                    </td>

                    <td>
                      {formatTime(item.created_at)}
                    </td>

                    <td>
                      {item.explorer_url ? (
                        <a
                          href={item.explorer_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Explorer ↗
                        </a>
                      ) : (
                        <span
                          className="rejection-reason"
                          title={item.reason || ''}
                        >
                          {item.reason || 'No transaction'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <footer>
        ArcAgent Pay · Built on Arc · USDC-native agent payments
      </footer>
    </main>
  )
}

export default App