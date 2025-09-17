# Procurement Copilot Frontend

A modern Next.js 14 frontend application for the Procurement Copilot platform, featuring AI-powered tender monitoring with email alerts, user management, and subscription billing.

## Features

- **Modern UI**: Built with Next.js 14, TypeScript, and Tailwind CSS
- **Authentication**: Clerk integration with email magic link authentication
- **Payments**: Stripe integration for subscription billing
- **Real-time Dashboard**: Live tender feed with filtering and search
- **Saved Filters**: Create and manage custom tender filters
- **Responsive Design**: Mobile-first design with beautiful UI components

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Clerk
- **Payments**: Stripe
- **Icons**: Heroicons, Lucide React
- **UI Components**: Headless UI

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see main README)
- Clerk account and API keys
- Stripe account and API keys

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd procurement-copilot/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env.local
   ```

4. **Configure environment variables**
   Edit `.env.local` with your actual values:
   ```env
   # Clerk Authentication
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here
   CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
   NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
   NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
   NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/app
   NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/app

   # Stripe
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
   STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

   # Backend API
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

### Development

1. **Start the development server**
   ```bash
   npm run dev
   ```

2. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Building for Production

```bash
npm run build
npm start
```

## Configuration

### Clerk Setup

1. **Create a Clerk account** at [clerk.com](https://clerk.com)
2. **Create a new application**
3. **Configure authentication methods**:
   - Enable email magic link
   - Set up redirect URLs
4. **Get your API keys** from the Clerk dashboard
5. **Add keys to environment variables**

### Stripe Setup

1. **Create a Stripe account** at [stripe.com](https://stripe.com)
2. **Get your API keys** from the Stripe dashboard
3. **Create products and prices**:
   ```bash
   # Using Stripe CLI or dashboard
   stripe products create --name "Starter Plan" --description "1 filter, daily alerts"
   stripe prices create --product prod_xxx --unit-amount 9900 --currency eur --recurring interval=month
   ```
4. **Set up webhooks**:
   - Endpoint: `https://your-domain.com/api/stripe/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, etc.
5. **Add keys to environment variables**

### Backend Connection

Ensure your backend API is running and accessible at the URL specified in `NEXT_PUBLIC_API_URL`.

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── api/               # API routes (Stripe webhooks)
│   │   ├── app/               # Protected dashboard pages
│   │   ├── account/           # Account management
│   │   ├── pricing/           # Pricing page
│   │   └── layout.tsx         # Root layout
│   ├── components/            # Reusable UI components
│   │   └── CreateFilterModal.tsx
│   └── lib/                   # Utilities and configurations
│       ├── api.ts            # API client
│       └── utils.ts          # Helper functions
├── public/                    # Static assets
├── env.example               # Environment variables template
├── vercel.json              # Vercel deployment config
└── package.json
```

## Key Components

### API Client (`src/lib/api.ts`)
- Centralized API communication with the backend
- Automatic user email header injection
- Type-safe request/response handling
- Error handling and retry logic

### Authentication
- Clerk integration with email magic link
- Automatic user creation in backend
- Protected routes and middleware
- User context throughout the app

### Dashboard (`src/app/app/`)
- Real-time tender feed
- Saved filters management
- Upcoming deadlines calendar
- Statistics and usage metrics

### Filter Management
- Create/edit modal with comprehensive form
- Keyword, CPV code, and country filtering
- Value range and frequency settings
- Real-time validation and error handling

### Billing Integration
- Stripe Checkout for subscriptions
- Billing portal for account management
- Webhook handling for subscription events
- Plan-based feature restrictions

## Deployment

### Vercel (Recommended)

1. **Connect your repository** to Vercel
2. **Set environment variables** in Vercel dashboard
3. **Deploy automatically** on push to main branch

### Other Platforms

The app can be deployed to any platform that supports Next.js:
- Netlify
- Railway
- DigitalOcean App Platform
- AWS Amplify

## Testing

### Manual Testing

1. **Authentication Flow**:
   - Sign up with email
   - Verify magic link
   - Sign in/out functionality

2. **Dashboard Features**:
   - View tender feed
   - Create/edit filters
   - Check upcoming deadlines

3. **Billing Flow**:
   - Select a plan on pricing page
   - Complete Stripe checkout
   - Access billing portal

### Test Cards (Stripe)

Use these test card numbers for testing payments:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure backend CORS is configured for frontend URL
   - Check `NEXT_PUBLIC_API_URL` is correct

2. **Authentication Issues**:
   - Verify Clerk keys are correct
   - Check redirect URLs in Clerk dashboard
   - Ensure backend creates users automatically

3. **Stripe Issues**:
   - Verify Stripe keys are for the correct environment (test/live)
   - Check webhook endpoint is accessible
   - Ensure webhook events are configured

4. **API Connection**:
   - Verify backend is running
   - Check API URL in environment variables
   - Ensure backend endpoints are accessible

### Debug Mode

Enable debug logging by setting:
```env
NEXT_PUBLIC_DEBUG=true
```

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Run tests and linting**
5. **Submit a pull request**

### Code Style

- Use TypeScript for all new code
- Follow Next.js best practices
- Use Tailwind CSS for styling
- Write meaningful commit messages

## License

This project is licensed under the MIT License - see the main README for details.