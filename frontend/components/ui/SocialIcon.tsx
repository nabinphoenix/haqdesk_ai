"use client";

import {
    Facebook,
    Instagram,
    MessageCircle,
    MoreHorizontal
} from "lucide-react";

interface SocialIconProps {
    platform: "WhatsApp" | "Instagram" | "Facebook" | string;
    className?: string;
}

export default function SocialIcon({ platform, className = "w-4 h-4" }: SocialIconProps) {
    const iconProps = {
        className: className,
        strokeWidth: 2, // Specification Requirement: 2px stroke
    };

    switch (platform) {
        case "WhatsApp":
            return <MessageCircle {...iconProps} className={`${className} text-[#25D366]`} />;
        case "Instagram":
            // Premium Gradient handling for Instagram
            return (
                <div className="relative">
                    <Instagram {...iconProps} className={`${className} text-[#E4405F]`} />
                    <div className="absolute inset-0 bg-gradient-to-tr from-[#f09433] via-[#dc2743] to-[#bc1888] opacity-20 blur-[2px] rounded-full" />
                </div>
            );
        case "Facebook":
            return <Facebook {...iconProps} className={`${className} text-[#2563EB]`} />; // Secondary Action Blue mapping
        default:
            return <MoreHorizontal {...iconProps} className={`${className} text-[#64748B]`} />;
    }
}



