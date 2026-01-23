
"use client";

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { ThemeToggle } from "@/components/theme-toggle";

const RootLayout = ({ children }) => {
    return (
        <SidebarProvider>
            <AppSidebar />
            <main className="flex-1">
                <header className="flex h-14 items-center justify-between gap-4 border-b px-4">
                    <SidebarTrigger />
                    <ThemeToggle />
                </header>
                <div className="p-4">
                    {children}
                </div>
            </main>
        </SidebarProvider>
    );
};

export default RootLayout;