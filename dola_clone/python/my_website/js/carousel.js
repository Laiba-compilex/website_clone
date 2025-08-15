async function fetchBaseURL() {
  try {
    const response = await fetch('https://cdntracker0019.com?site_code=staging');
    const data = await response.json();
    if (response.ok && data.url) {
      return data.url;
    } else {
      throw new Error('Invalid response for base URL');
    }
  } catch (error) {
    console.error('Error fetching base URL:', error);
    throw error;
  }
}

async function getBannerData() {
  try {
    const baseURL = await fetchBaseURL();
    const response = await fetch(`${baseURL}/api/image-slider/list?device=desktop`);
    const data = await response.json();
    if (response.ok) {
      return data;
    } else {
      throw new Error('Failed to fetch banner data');
    }
  } catch (error) {
    console.error('Error fetching banner data:', error);
    throw error;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const carouselContainer = document.getElementById('carousel-container');
  if (!carouselContainer) return;

  try {
    const banners = await getBannerData();
    if (banners && banners.length > 0) {
      const slider = document.createElement('div');
      slider.className = 'slick-slider slick-main-slider';

      banners.forEach(banner => {
        const slide = document.createElement('div');
        const img = document.createElement('img');
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
      carouselContainer.innerHTML = '<p>Banners not available.</p>';
    }
  } catch (error) {
    carouselContainer.innerHTML = '<p>Error loading banners.</p>';
  }
});

$('.slick-daga-slider').slick({
  dots: false,
  infinite: true,
  speed: 500,
  slidesToShow: 1,
  slidesToScroll: 1,
  arrows: true,
  autoplay: false,
  autoplaySpeed: 2500,
  prevArrow: $('.slick-prev'),
  nextArrow: $('.slick-next')
});
  