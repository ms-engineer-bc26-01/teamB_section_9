import Link from "next/link";

export function Footer() {
    return (
        <footer className="hidden border-t border-[#E8DED4] bg-white md:block">
            <div className="mx-auto max-w-[390px] px-4 py-6 text-center">
                <p className="text-xs text-[#8C715C]">
                    Climo helps you choose outfits from your own closet.
                </p>
                <nav className="mt-3 flex items-center justify-center gap-4 text-[11px] text-[#8C715C]">
                    <Link href="/terms" className="underline-offset-4 hover:underline">
                        利用規約
                    </Link>
                    <Link href="/privacy" className="underline-offset-4 hover:underline">
                        プライバシーポリシー
                    </Link>
                </nav>
                <p className="mt-1 text-[11px] text-[#A99A8B]">© 2026 Climo</p>
            </div>
        </footer>
    );
}
