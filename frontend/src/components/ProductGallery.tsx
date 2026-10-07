"use client";

import Image from "next/image";
import { useState } from "react";

import type { ProductImage } from "@/lib/api";

export function ProductGallery({ images, title }: { images: ProductImage[]; title: string }) {
  const [activeIndex, setActiveIndex] = useState(0);

  if (images.length === 0) {
    return <div className="relative aspect-square rounded-md bg-neutral-100" />;
  }

  const active = images[activeIndex] ?? images[0];

  return (
    <div>
      <div className="relative aspect-square overflow-hidden rounded-md bg-neutral-100">
        {/* The first image is this route's LCP, so preload it. Later picks swap
            in on click, where lazy loading is what we want. */}
        <Image
          src={active.url}
          alt={active.alt || title}
          fill
          priority={activeIndex === 0}
          sizes="(max-width: 1024px) 100vw, 50vw"
          className="object-cover"
        />
      </div>
      {images.length > 1 ? (
        <div className="mt-3 flex gap-3">
          {images.map((image, index) => (
            <button
              key={image.url}
              type="button"
              onClick={() => setActiveIndex(index)}
              aria-label={`Show image ${index + 1}`}
              aria-current={index === activeIndex}
              className={`relative h-16 w-16 overflow-hidden rounded-md border ${
                index === activeIndex ? "border-emerald-700" : "border-neutral-200"
              }`}
            >
              <Image
                src={image.url}
                alt={image.alt || title}
                fill
                sizes="64px"
                className="object-cover"
              />
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
