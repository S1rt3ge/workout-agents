import { Navbar } from "@/components/navbar"
import { HeroSection } from "@/components/hero-section"
import { FeaturesSection } from "@/components/features-section"
import { PipelineSection } from "@/components/pipeline-section"
import { CTASection } from "@/components/cta-section"

export default function Home() {
  return (
    <main className="relative">
      <Navbar />
      <HeroSection />
      <div id="features">
        <FeaturesSection />
      </div>
      <div id="pipeline">
        <PipelineSection />
      </div>
      <CTASection />
    </main>
  )
}
