async function fetchBaseURL() {
  try {
    const response = await fetch(
      "https://cdntracker0019.com?site_code=staging"
    );
    const data = await response.json();
    if (response.ok && data.url) {
      return data.url;
    } else {
      throw new Error("Invalid response for base URL");
    }
  } catch (error) {
    console.error("Error fetching base URL:", error);
    throw error;
  }
}
const banners = [
  {
    image_url: "./images/40433064-908f-44cb-90f3-1367af4413f0.jpg",
    title: "Banner 1",
  },
  {
    image_url: "./images/31443127-ee2b-4b8f-bac1-59d8b45714f0.jpg",
    title: "Banner 2",
  },
  {
    image_url: "./images/507f41ad-1287-483e-9075-696dcbc4d4fd.jpg",
    title: "Banner 3",
  },
  {
    image_url: "./images/170df58b-0899-4bfc-bce5-16938e4f27eb.jpg",
    title: "Banner 4",
  },
  {
    image_url: "./images/82c4a721-4a76-4d21-bdc7-23bae942a10a.jpg",
    title: "Banner 5",
  },
  {
    image_url: "./images/27ee30da-29d6-4b42-9cfd-c89e1f3e6304.jpg",
    title: "Banner 6",
  },
  {
    image_url: "./images/75b13e9c-2d07-4810-a768-8a08ea2a35ca.jpg",
    title: "Banner 7",
  },

];
async function getBannerData() {
  try {
    const baseURL = await fetchBaseURL();
    const response = await fetch(
      `${baseURL}/api/image-slider/list?device=desktop`
    );
    const data = await response.json();
    if (response.ok) {
      return data;
    } else {
      throw new Error("Failed to fetch banner data");
    }
  } catch (error) {
    console.error("Error fetching banner data:", error);
    throw error;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const carouselContainer = document.getElementById("carousel-container");
  if (!carouselContainer) return;

  try {
    // const banners = await getBannerData();
    console.log("Banners:", banners);
    if (banners && banners.length > 0) {
      const slider = document.createElement("div");
      slider.className = "slick-slider slick-main-slider";

      banners.forEach((banner) => {
        const slide = document.createElement("div");
        const img = document.createElement("img");
        img.src = banner.image_url;
        img.alt = banner.title;
        slide.appendChild(img);
        slider.appendChild(slide);
      });

      carouselContainer.appendChild(slider);

      // Initialize Slick Carousel
      $(slider).slick({
        dots: true,
        infinite: true,
        speed: 500,
        slidesToShow: 1,
        slidesToScroll: 1,
        autoplay: true,
        autoplaySpeed: 3000,
        arrows: false,
      });
    } else {
      carouselContainer.innerHTML = "<p>Banners not available.</p>";
    }
  } catch (error) {
    carouselContainer.innerHTML = "<p>Error loading banners.</p>";
  }
});

$(".slick-daga-slider").slick({
  dots: false,
  infinite: true,
  speed: 500,
  slidesToShow: 1,
  slidesToScroll: 1,
  arrows: true,
  autoplay: false,
  autoplaySpeed: 2500,
  prevArrow: $(".slick-prev"),
  nextArrow: $(".slick-next"),
});
