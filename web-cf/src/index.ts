import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { staticRoute } from './routes/static'
import { apiRoute } from './routes/api'
import { HomePage } from './templates/HomePage'
import { html } from 'hono/html'

const app = new Hono<{
  Bindings: {
    MODAL_API_URL: string
    API_KEY: string
    STATIC_BUCKET: R2Bucket
  }
}>()

// CORS configuration for cross-origin requests to Modal API
app.use('/api/*', cors({
  origin: ['http://localhost:8787', 'https://vibe.yourdomain.com'],
  allowHeaders: ['Content-Type', 'Authorization'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
}))

// Routes
app.route('/static', staticRoute)
app.route('/api', apiRoute)

// Health check
app.get('/health', (c) => c.json({ status: 'ok', timestamp: Date.now() }))

// Home page route
app.get('/', async (c) => {
  try {
    // Fetch data from Modal API
    const appsResponse = await fetch(`${c.env.MODAL_API_URL}/api/apps`)
    if (!appsResponse.ok) {
      throw new Error(`API request failed: ${appsResponse.status}`)
    }
    const apps = await appsResponse.json()

    return c.html(HomePage({ apps }))
  } catch (error) {
    console.error('Error fetching apps:', error)
    // Fallback to error page
    return c.html(html`
      <!DOCTYPE html>
      <html>
        <head><title>Vibe App - Error</title></head>
        <body>
          <h1>Service Temporarily Unavailable</h1>
          <p>Please try again in a moment.</p>
        </body>
      </html>
    `, 503)
  }
})

// App detail page route
app.get('/app/:id', async (c) => {
  const appId = c.req.param('id')
  try {
    const appResponse = await fetch(`${c.env.MODAL_API_URL}/api/apps/${appId}`)
    if (!appResponse.ok) {
      return c.notFound()
    }
    const app = await appResponse.json()

    return c.html(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${app.name} - Vibe App</title>
          <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
          <div class="container">
            <h1>${app.name}</h1>
            <p>${app.description}</p>
            <div id="app-content">${app.content || 'Loading...'}</div>
          </div>
          <script src="/static/js/app.js"></script>
        </body>
      </html>
    `)
  } catch (error) {
    console.error('Error fetching app:', error)
    return c.html(`
      <!DOCTYPE html>
      <html>
        <head><title>Vibe App - Error</title></head>
        <body>
          <h1>App Not Found</h1>
          <p>The requested app could not be loaded.</p>
        </body>
      </html>
    `, 404)
  }
})

export default app
