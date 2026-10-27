type AdSlotVariant = "header" | "sidebar" | "inline";

const BASE =
  "flex items-center justify-center rounded-lg border border-dashed border-[#6d5a91] bg-transparent text-center";

const VARIANTS: Record<AdSlotVariant, string> = {
  header: "h-[90px] w-full max-w-[728px] mx-auto",
  sidebar: "hidden h-[250px] w-[300px] shrink-0 lg:flex sticky top-24",
  inline: "col-span-full h-[90px] w-full",
};

export function AdSlot({ variant }: { variant: AdSlotVariant }) {
  return (
    <div
      role="complementary"
      aria-label="Espaço publicitário"
      className={`${BASE} ${VARIANTS[variant]}`}
    >
      <span className="text-sm font-normal text-[#b8a9cc]">
        Espaço publicitário
      </span>
    </div>
  );
}
