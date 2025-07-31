{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.requests
    pkgs.python311Packages.discordpy
    pkgs.python311Packages.nest_asyncio
  ];
}
