"use client"

import { Bot, User } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import Image from "next/image"

interface Message {
  id: number
  content: string
  sender: "user" | "bot"
  timestamp: Date
}

interface ChatBubbleProps {
  message: Message
  isTyping?: boolean
}

export function ChatBubble({ message, isTyping = false }: ChatBubbleProps) {
  const isBot = message.sender === "bot"

  return (
    <div className={cn("flex gap-3 max-w-[80%]", isBot ? "justify-start" : "justify-end ml-auto")}>
      {isBot && (
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Image src="/logo.png" height={32} width={32} alt="BukidMate's Logo" className="w-10 h-10" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={cn("flex flex-col gap-1", isBot ? "items-start" : "items-end")}>
        <Card className={cn("max-w-full", isBot ? "bg-muted" : "bg-primary text-primary-foreground")}>
          <CardContent className="p-3">
            {isTyping ? (
              <div className="flex items-center gap-1">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                </div>
              </div>
            ) : (
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
            )}
          </CardContent>
        </Card>

        <span className="text-xs text-muted-foreground px-1">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>

      {!isBot && (
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="bg-secondary">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}