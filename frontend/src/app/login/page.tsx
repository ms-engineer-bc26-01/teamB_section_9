import LoginPageClient from "./LoginPageClient";

type Props = {
  searchParams: Promise<{
    redirect?: string;
  }>;
};

export default async function LoginPage({ searchParams }: Props) {
  const params = await searchParams;
  const redirectParam = params.redirect;
  const redirectTo =
    redirectParam &&
    redirectParam.startsWith("/") &&
    !redirectParam.startsWith("//") &&
    !redirectParam.startsWith("/login")
      ? redirectParam
      : "/";

  return <LoginPageClient redirectTo={redirectTo} />;
}
