import Image from 'next/image';

export function Logo({ className }: { className?: string }) {
  // Extract width/height from className if possible, or default to a standard size
  // Since className usually handles width/height in Tailwind (e.g. w-6 h-6), 
  // we need to ensure the Image component respects that constraint.
  // Using "fill" with object-contain is often easiest for responsive containers,
  // but for a simple logo replacement, explicit width/height with "w-auto" might be safer 
  // if the container isn't relative.

  // However, "className" is often passed like "h-6 w-6". 
  // Simple <img> tag or unoptimized Image is easiest for drop-in replacement of SVG.
  // Let's use a simple img tag for maximum compatibility with existing SVG usage expectations 
  // (which scales with font-size/width), or a relative wrapper.

  return (
    <div className={`relative ${className} flex items-center`}>
      <Image
        src="/logo.png"
        alt="SupaAgent"
        width={0}
        height={0}
        sizes="100vw"
        className="h-full w-auto object-contain"
        priority
      />
    </div>
  );
}

