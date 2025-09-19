'use client'

import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <img src="/logo.svg" alt="TenderPulse" className="h-12 w-auto" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>
          Start your free trial
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Monitor 139+ active EU procurement opportunities
        </p>
      </div>
      
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <SignUp 
            appearance={{
              elements: {
                formButtonPrimary: 'bg-[#003399] hover:bg-[#002266]',
                card: 'shadow-none'
              }
            }}
          />
        </div>
      </div>
      
      <div className="mt-8 text-center text-xs text-gray-500">
        TenderPulse is an independent service and is not affiliated with the European Union or its institutions.
      </div>
    </div>
  )
}
