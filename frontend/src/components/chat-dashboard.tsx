"use client"
import { Bot, Leaf, Settings, MapPin, Wheat } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  SidebarSeparator,
} from "@/components/ui/sidebar"
import { ChatInterface } from "@/components/chat-interface"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import Image from "next/image"

const philippinesRegions = [
  "Northern Mindanao",
  "Eastern Visayas",
  "Ilocos Region",
  "Bicol Region",
  "Western Visayas",
  "Cagayan Valley",
  "Central Luzon",
  "Davao Region",
  "CALABARZON",
  "Central Visayas",
  "Zamboanga Peninsula",
  "SOCCSKSARGEN"
]

const availableCrops = [
  "Sugarcane",
  "Banana",
  "Coffee",
  "Garlic",
  "Coconut",
  "Pineapple",
  "Tomato",
  "Tobacco",
  "Rice",
  "Mango",
  "Onion",
  "Corn"
]

export function ChatDashboard() {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <Sidebar className="border-r">
          <SidebarHeader className="border-b p-4">
            <div className="flex items-center gap-2">
              <Leaf className="h-6 w-6 text-primary" />
              <h1 className="text-sm font-semibold">Region & Crop Directory</h1>
            </div>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Philippines Regions
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {philippinesRegions.map((region, index) => (
                    <SidebarMenuItem key={index}>
                      <SidebarMenuButton className="text-sm py-1 h-auto">
                        <span className="truncate">{region}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarSeparator />

            <SidebarGroup>
              <SidebarGroupLabel className="flex items-center gap-2">
                <Wheat className="h-4 w-4" />
                Available Crops
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {availableCrops.map((crop, index) => (
                    <SidebarMenuItem key={index}>
                      <SidebarMenuButton className="text-sm py-1 h-auto">
                        <span className="truncate">{crop}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="border-t p-4">
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <Settings className="h-4 w-4" />
                  <span>Settings</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarFooter>
        </Sidebar>

        <SidebarInset className="flex-1">
          <header className="flex h-16 items-center gap-2 border-b px-4">
            <SidebarTrigger />
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback>
                  <Image src="/logo.png" height={32} width={32} alt="BukidMate's Logo" className="w-10 h-10" />
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="font-semibold">BukidMate</h2>
                <p className="text-xs text-muted-foreground">Active</p>
              </div>
            </div>
          </header>

          <ChatInterface />
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
