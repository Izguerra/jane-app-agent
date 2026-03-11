import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export function PricingCard({
    name,
    price,
    interval,
    features,
    priceId,
    popular = false,
    isEnterprise = false,
}: {
    name: string;
    price: number | null;
    interval: string;
    features: string[];
    priceId?: string;
    popular?: boolean;
    isEnterprise?: boolean;
}) {
    return (
        <div
            className={`relative pt-6 pb-8 px-6 rounded-2xl ${popular
                ? 'bg-gradient-to-b from-blue-50 to-white border-2 border-blue-500 shadow-xl'
                : 'bg-white border border-gray-200 shadow-sm'
                }`}
        >
            {popular && (
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                        Most Popular
                    </span>
                </div>
            )}

            <h2 className="text-2xl font-bold text-gray-900 mb-2">{name}</h2>

            {!isEnterprise && (
                <p className="text-sm text-gray-600 mb-4">
                    14 day free trial
                </p>
            )}

            {isEnterprise && (
                <p className="text-sm text-gray-600 mb-4 invisible">
                    Placeholder
                </p>
            )}

            <div className="mb-6">
                {price !== null ? (
                    <>
                        <p className="text-5xl font-bold text-gray-900">${price / 100}</p>
                        <p className="text-gray-600 mt-1">per {interval}</p>
                    </>
                ) : (
                    <>
                        <p className="text-5xl font-bold text-gray-900">Custom</p>
                        <p className="text-gray-600 mt-1">Contact sales</p>
                    </>
                )}
            </div>

            <ul className="space-y-3 mb-8">
                {features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                        <Check
                            className={`h-5 w-5 ${popular ? 'text-blue-600' : 'text-blue-500'
                                } mr-3 mt-0.5 flex-shrink-0`}
                        />
                        <span className="text-gray-700">{feature}</span>
                    </li>
                ))}
            </ul>

            {isEnterprise ? (
                <a
                    href="mailto:sales@supaagent.com"
                    className={`block w-full text-center py-3 px-4 rounded-full font-medium transition-colors ${popular
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-900 text-white hover:bg-gray-800'
                        }`}
                >
                    Contact Sales
                </a>
            ) : (
                <Button
                    asChild
                    className={`w-full py-3 px-4 rounded-full font-medium transition-colors ${popular
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-900 text-white hover:bg-gray-800'
                        }`}
                >
                    <Link href={`/sign-up?redirect=checkout&priceId=${priceId}`}>
                        Get Started
                    </Link>
                </Button>
            )}
        </div>
    );
}
