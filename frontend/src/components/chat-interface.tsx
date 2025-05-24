"use client"

import { useState, useRef, useEffect } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ChatBubble } from "@/components/chat-bubble"
import { ChatInput } from "./chat-input"

interface Message {
  id: number
  content: string
  sender: "user" | "bot"
  timestamp: Date
}

const date = new Date();

const monthNames = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

const day = date.getDate();
const month = date.getMonth();
const year = date.getFullYear();

const initialMessages: Message[] = [
  {
    id: 1,
    content: "🌱 Hi, ako si BukidMate! Ako ang inyong kaagapay sa pagtatanim.\nPara makuha ang pinakaswak na presyo ng ani mo, pakitype lang:\n\ \n\"Region, Crop\"\n📍 Halimbawa: \"Ilocos Norte, Mais\"\n \nTara, simulan na natin! 💪🌾",
    sender: "bot",
    timestamp: new Date(Date.now() - 300000),
  },
  {
    id: 2,
    content: "Central Luzon, Tomato",
    sender: "user",
    timestamp: new Date(Date.now() - 240000),
  },
  {
    id: 3,
    content:
      `Sa Central Luzon ngayong ${monthNames[month] + " " + day + " " + year}, ang inaasahang presyo ng Tomato ay ₱65.27. Normal weather conditions. Ang presyo ng kamatis sa Central Luzon ay nanatiling matatag sa 50 PHP/kg sa nakaraang tatlong araw. Inaasahan na ang lagay ng panahon ngayong araw (2024-06-12) ay magiging 'Sunny' na may average na temperatura na 34.0°C. Ang mainit at maaraw na panahon ay maaaring makaapekto sa ani, ngunit kung ang supply ay mananatiling pareho, inaasahan na ang presyo ay maaaring manatili sa 50 PHP/kg. Subaybayan ang lagay ng panahon at ang epekto nito sa ani upang maplano ang inyong bentahan.`,
    sender: "bot",
    timestamp: new Date(Date.now() - 180000),
  },
  {
    id: 4,
    content:
      `Gusto mo ba ibenta Tomato sa Central Luzon? Mag type ng 'OO' upang ituloy.`,
    sender: "bot",
    timestamp: new Date(Date.now() - 180000),
  }
]

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [isTyping, setIsTyping] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      id: messages.length + 1,
      content,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsTyping(true)
  }

  const handleApiResponse = (data: any) => {
    setIsTyping(false)
    
    if (data.message) {
      const mainMessage: Message = {
        id: messages.length + 2,
        content: data.message,
        sender: "bot",
        timestamp: new Date(),
      }
      
      setMessages((prev) => [...prev, mainMessage])
    }
    
    // Add the follow-up message if it exists
    if (data.follow_up) {
      setTimeout(() => {
        const followUpMessage: Message = {
          id: messages.length + 3,
          content: data.follow_up,
          sender: "bot",
          timestamp: new Date(),
        }
        
        setMessages((prev) => [...prev, followUpMessage])
      }, 500)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}
          {isTyping && (
            <ChatBubble
              message={{
                id: 0,
                content: "Typing...",
                sender: "bot",
                timestamp: new Date(),
              }}
              isTyping={true}
            />
          )}
        </div>
      </ScrollArea>

      <div className="border-t p-4">
        <div className="max-w-4xl mx-auto">
          <ChatInput 
            onSendMessage={handleSendMessage}
            onApiResponse={handleApiResponse}
          />
        </div>
      </div>
    </div>
  )
}