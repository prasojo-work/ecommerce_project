import Link from "next/link";

export default function HomePage() {
  return (
    <section className="py-12">
      <p className="text-sm font-medium tracking-widest text-emerald-800 uppercase">
        Small-space living
      </p>
      <h1 className="mt-3 max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
        Everyday home goods, designed to fit.
      </h1>
      <p className="mt-4 max-w-xl text-neutral-600">
        Affordable, well-made furniture and homeware for apartments and small homes.
      </p>
      <Link
        href="/products"
        className="mt-8 inline-block rounded-md bg-emerald-800 px-6 py-3 text-sm font-medium text-white transition hover:bg-emerald-900"
      >
        Shop the collection
      </Link>
    </section>
  );
}
