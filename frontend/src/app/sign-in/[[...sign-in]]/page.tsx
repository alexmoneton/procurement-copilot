'use client'

import { SignIn } from '@clerk/nextjs'
import Image from 'next/image'

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Image src="/logo.svg" alt="TenderPulse" width={48} height={48} className="h-12 w-auto" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>
          Sign in to TenderPulse
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Access your EU procurement dashboard
        </p>
      </div>
      
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <SignIn 
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
