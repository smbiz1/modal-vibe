import { html } from 'hono/html'

interface App {
  id: string
  name?: string
  description?: string
  url?: string
  title?: string
  is_featured?: boolean
}

export const HomePage = ({ apps }: { apps: App[] }) => {
  const appCount = apps.length
  const featuredApps = apps.filter(app => app.is_featured).slice(0, 6)
  const regularApps = apps.filter(app => !app.is_featured || !featuredApps.find(f => f.id === app.id))

  return html`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Modal Vibe - Create Apps by Chatting with AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/css/style.css">
        <link rel="stylesheet" href="https://cdn.tailwindcss.com">
        <style>
          html {
            scroll-behavior: smooth;
            overflow-x: hidden;
            max-width: 100vw;
          }

          body {
            overflow-x: hidden;
            max-width: 100vw;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
          }

          /* Gradient text */
          .gradient-text {
            background: linear-gradient(135deg, #00f10f, #00ffff, #ffff00);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-size: 200% 200%;
            animation: gradientShift 3s ease-in-out infinite;
          }

          @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
          }

          /* Flip counter styles */
          .flip-counter {
            display: flex;
            gap: 4px;
            perspective: 1000px;
          }

          .flip-digit-container {
            position: relative;
            width: 60px;
            height: 80px;
          }

          .flip-digit {
            width: 100%;
            height: 100%;
            position: relative;
          }

          .flip-card {
            width: 100%;
            height: 100%;
            position: relative;
            transform-style: preserve-3d;
          }

          .flip-card-inner {
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1a1a2e, #0f0f1e);
            border-radius: 12px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), inset 0 2px 4px rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            font-weight: 900;
            color: #fff;
            text-shadow: 0 0 20px rgba(34, 197, 94, 0.8);
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
          }

          .flip-card-front, .flip-card-back {
            width: 100%;
            height: 100%;
            position: absolute;
            backface-visibility: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
          }

          .flip-card-front { z-index: 2; }
          .flip-card-back { transform: rotateX(180deg); }

          /* Button styles */
          .btn-modal {
            background: linear-gradient(135deg, #00f10f, #00ffff);
            border: none;
            border-radius: 8px;
            color: #000;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 241, 15, 0.3);
          }

          .btn-modal:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 241, 15, 0.4);
          }

          .btn-modal:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
          }
        </style>
      </head>
      <body class="bg-black text-white min-h-screen">
        <div class="text-center py-12 md:py-20 pb-16 md:pb-24">
          <!-- Hero Section -->
          <div class="mb-8 md:mb-16 min-h-[300px] md:min-h-[400px]">
            <h1 class="text-5xl md:text-7xl font-medium tracking-tight mb-4 md:mb-6 gradient-text">
              Modal Vibe
            </h1>
            <p class="text-lg md:text-xl font-normal tracking-tight text-[#8491a5] mb-8 md:mb-12 max-w-2xl mx-auto px-4">
              Vibe code your websites with AI, powered by Modal Sandboxes
            </p>

            <div class="flex justify-center mb-8">
              <div class="bg-white/5 rounded-xl p-4 md:p-8 max-w-xl w-full mx-4 md:mx-auto shadow-2xl border border-[rgba(255,255,255,0.05)] backdrop-blur-md">
                <div class="flex items-center space-x-3 mb-4">
                  <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                  <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <div class="w-3 h-3 bg-[#00f10f] rounded-full"></div>
                  <div class="text-sm text-[#8491a5] ml-2 tracking-tight">Create New App</div>
                </div>

                <div class="relative mb-6">
                  <input
                    type="text"
                    id="appPrompt"
                    placeholder="What's the vibe today?"
                    class="w-full px-4 py-3 border border-[rgba(255,255,255,0.1)] rounded-lg bg-white/5 text-gray-300 placeholder-gray-500 tracking-tight focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[#000000] disabled:border-black"
                  >
                </div>

                <button id="createAppBtn" onclick="createApp()" class="btn-modal w-full py-3 px-4 md:px-8 rounded-lg text-base md:text-lg transition duration-200 font-medium tracking-tight disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Create App
                </button>

                <div id="spinner" class="hidden">
                  <div class="flex items-center justify-center space-x-3 mt-4">
                    <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-[#00f10f]"></div>
                    <p class="text-[#8491a5] tracking-tight">Creating your app...</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Collaborate and Create Section -->
          <div class="mt-12 md:mt-20">
            <div class="rounded-xl p-4 md:p-8 bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)] mx-2 md:mx-0">
              <h2 class="text-2xl md:text-3xl font-medium tracking-tight mb-4 gradient-text">
                Collaborate and Create
              </h2>

              <!-- Giant Flip Counter -->
              <div class="flip-counter-container my-8 md:my-12 flex flex-col md:flex-row justify-center items-center gap-4 md:gap-0">
                <div class="flip-counter">
                  ${Array.from(String(Math.min(appCount, 999)).padStart(3, '0')).map(digit => `
                    <div class="flip-digit-container">
                      <div class="flip-digit">
                        <div class="flip-card">
                          <div class="flip-card-inner">
                            <div class="flip-card-front">${digit}</div>
                            <div class="flip-card-back">${digit}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  `).join('')}
                </div>
                <div class="flip-counter-label md:ml-8">
                  <div class="text-4xl md:text-6xl font-bold text-white/90">APPS</div>
                  <div class="text-lg md:text-xl text-[#8491a5] mt-1 md:mt-2">AND COUNTING</div>
                </div>
              </div>

              <p class="text-[#8491a5] mb-0 text-base md:text-lg tracking-tight px-2 md:px-0">
                You can see what other people are building and build on top of their work.
              </p>
            </div>
          </div>

          <!-- Apps Content Section -->
          <div class="mt-8">
            <div id="appsContent">
              ${apps.length > 0 ? `
                ${featuredApps.length > 0 ? `
                  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 mb-8">
                    ${featuredApps.map(app => `
                      <a href="/app/${app.id}" class="transform transition-all duration-200 hover:scale-[1.02] block">
                        <div class="border border-gray-700/50 rounded-xl bg-[rgba(255,255,255,0.02)] backdrop-blur-md overflow-hidden aspect-[4/3] relative">
                          <div class="absolute inset-0 w-full h-full bg-gray-900/50 flex items-center justify-center">
                            <div class="w-8 h-8 border-2 border-gray-600 border-t-green-500 rounded-full animate-spin"></div>
                          </div>
                          ${app.title ? `
                            <div class="absolute bottom-0 left-0 right-0 bg-black p-2 z-10">
                              <div class="text-xs font-light italic tracking-wide text-white text-left" title="${app.title}">
                                ${app.title.length > 50 ? app.title.substring(0, 15) + '...' : app.title}
                              </div>
                            </div>
                          ` : ''}
                        </div>
                      </a>
                    `).join('')}
                  </div>
                ` : ''}

                ${regularApps.length > 0 ? `
                  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 md:gap-4 mb-8">
                    ${regularApps.slice(0, 24).map(app => `
                      <a href="/app/${app.id}" class="transform transition-all duration-200 hover:scale-[1.02] block">
                        <div class="border border-gray-700/50 rounded-xl bg-[rgba(255,255,255,0.02)] backdrop-blur-md overflow-hidden aspect-[4/3] relative">
                          <div class="absolute inset-0 w-full h-full bg-gray-900/50 flex items-center justify-center">
                            <div class="w-8 h-8 border-2 border-gray-600 border-t-green-500 rounded-full animate-spin"></div>
                          </div>
                          ${app.title ? `
                            <div class="absolute bottom-0 left-0 right-0 bg-black p-2 z-10">
                              <div class="text-xs font-light italic tracking-wide text-white text-left" title="${app.title}">
                                ${app.title.length > 50 ? app.title.substring(0, 15) + '...' : app.title}
                              </div>
                            </div>
                          ` : ''}
                        </div>
                      </a>
                    `).join('')}
                  </div>
                ` : ''}
              ` : `
                <div class="border border-[rgba(255,255,255,0.05)] rounded-xl p-8 bg-[rgba(255,255,255,0.02)] backdrop-blur-md flex flex-col items-center justify-center h-64">
                  <h3 class="text-xl font-medium tracking-tight mb-2 gradient-text">No apps yet</h3>
                  <p class="text-[#8491a5] tracking-tight">Why don't you vibe one up?</p>
                </div>
              `}
            </div>
          </div>
        </div>

        <!-- Bottom Banner -->
        <div class="fixed bottom-0 left-0 right-0 bg-[rgba(0,0,0,0.8)] backdrop-blur-md border-t border-[rgba(255,255,255,0.1)] p-2 md:p-4 z-50">
          <div class="text-center flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3">
            <p class="text-xs sm:text-sm md:text-base text-[#8491a5] tracking-tight">
              There are <span class="text-[#00f10f] font-medium">${appCount}</span> people vibing right now
            </p>
            <div class="flex items-center gap-1 sm:gap-2">
              <div class="w-2 h-2 bg-[#00f10f] rounded-full animate-pulse"></div>
              <span class="text-xs text-[#00f10f] tracking-tight">LIVE</span>
            </div>
          </div>
        </div>

        <!-- Safely embed JSON data in a script tag -->
        <script type="application/json" id="apps-data">${JSON.stringify(apps)}</script>

        <script>
          // App creation functionality
          async function createApp() {
            const button = document.getElementById('createAppBtn');
            const spinner = document.getElementById('spinner');
            const createAppDiv = document.querySelector('.bg-white\\/5');
            const promptInput = document.getElementById('appPrompt');
            const prompt = promptInput.value.trim();

            if (prompt === '') {
              button.disabled = true;
              return;
            }

            createAppDiv.classList.add('shimmer');
            promptInput.disabled = true;
            button.style.display = 'none';
            spinner.classList.remove('hidden');

            try {
              const response = await fetch('/api/create', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt })
              });

              if (!response.ok) {
                const data = await response.json().catch(() => ({ error: 'Failed to create app' }));
                throw new Error(data.error || 'Failed to create app');
              }

              const data = await response.json();
              if (data.app_id) {
                window.location.href = '/app/' + data.app_id;
              } else {
                throw new Error('Invalid response from server');
              }
            } catch (error) {
              alert(error.message || 'Error creating app');
              createAppDiv.classList.remove('shimmer');
              button.style.display = 'inline-block';
              spinner.classList.add('hidden');
              promptInput.disabled = false;
            }
          }

          // Handle input and button state
          document.addEventListener('DOMContentLoaded', () => {
            const promptInput = document.getElementById('appPrompt');
            const createAppBtn = document.getElementById('createAppBtn');

            promptInput.addEventListener('input', (event) => {
              const hasValue = event.target.value.trim().length > 0;
              createAppBtn.disabled = !hasValue;
            });

            promptInput.addEventListener('keydown', (event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                if (event.target.value.trim().length > 0) {
                  createApp();
                }
              }
            });
          });
        </script>
      </body>
    </html>
  `
}
