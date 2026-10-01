"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

type RevealProps = {

    children: ReactNode;

    className?: string;

    delay?: number;

    direction?: "up" | "left" | "right" | "scale";

};

export default function Reveal({

    children,

    className = "",

    delay = 0,

    direction = "up",

}: RevealProps) {

    const ref = useRef<HTMLDivElement>(null);

    const [visible, setVisible] = useState(false);

    useEffect(() => {

        const element = ref.current;

        if (!element) {

            return;

        }

        const observer = new IntersectionObserver(

            ([entry]) => {

                if (entry.isIntersecting) {

                    setVisible(true);

                    observer.unobserve(element);

                }

            },

            {

                threshold: 0.12,

                rootMargin: "0px 0px -50px 0px",

            }

        );

        observer.observe(element);

        return () => observer.disconnect();

    }, []);

    const hiddenTransform = {

        up: "translateY(45px)",

        left: "translateX(-45px)",

        right: "translateX(45px)",

        scale: "scale(0.94)",

    }[direction];

    return (

        <div

            ref={ref}

            className={className}

            style={{ opacity: visible ? 1 : 0, transform: visible ? "translate3d(0, 0, 0) scale(1)" : hiddenTransform, transition: `opacity 700ms ease ${delay}ms, transform 700ms cubic-bezier(.22, 1, .36, 1) ${delay}ms`, }}

        >

            {children}

        </div>

    );

}