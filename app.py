import streamlit as st
import asyncio
import os
import glob
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import edge_tts

# Cấu hình giao diện Web dạng dọc phù hợp với màn hình iPhone
st.set_page_config(page_title="Tool Tạo Video Tự Động", page_icon="🎬", layout="centered")

st.title("🎬 Tool Tạo Video Ngắn Tự Động")
st.write("Dành cho các thiết bị di động và Phone Farm")

# 1. Khởi tạo các thư mục tạm để lưu ảnh, âm thanh và video ra
TEMP_DIR = "temp_assets"
os.makedirs(TEMP_DIR, exist_ok=True)

# Hàm bất đồng bộ để gọi API Edge-TTS (Giọng đọc AI của Microsoft cực hay và miễn phí)
async def generate_voiceover(text, output_path):
    # Sử dụng giọng Nam miền Bắc (NamMinhNeural) hoặc Nữ miền Nam (HoaiAnNeural)
    communicate = edge_tts.Communicate(text, "vi-VN-NamMinhNeural")
    await communicate.save(output_path)

# Hàm chính xử lý render video bằng MoviePy
def render_video(text_input, uploaded_images):
    audio_path = os.path.join(TEMP_DIR, "voiceover.mp3")
    output_video_path = os.path.join(TEMP_DIR, "final_output.mp4")
    
    # Bước A: Tạo giọng đọc từ văn bản
    with st.spinner("⏳ Đang chuyển văn bản thành giọng đọc AI..."):
        asyncio.run(generate_voiceover(text_input, audio_path))
    
    # Bước B: Xử lý file âm thanh để lấy thời lượng
    audio_clip = AudioFileClip(audio_path)
    total_duration = audio_clip.duration
    
    # Bước C: Lưu ảnh người dùng tải lên vào thư mục tạm
    with st.spinner("📸 Đang tối ưu hóa hình ảnh..."):
        saved_image_paths = []
        for i, uploaded_file in enumerate(uploaded_images):
            img_path = os.path.join(TEMP_DIR, f"img_{i}.png")
            with open(img_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_image_paths.append(img_path)
            
    # Bước D: Ghép ảnh thành video chạy khớp thời gian âm thanh
    with st.spinner("🎬 Đang render video dạng 1080x1920 (TikTok/Shorts)..."):
        num_images = len(saved_image_paths)
        duration_per_image = total_duration / num_images
        
        clips = []
        for img_path in saved_image_paths:
            # Tạo clip từ ảnh, đặt thời gian hiển thị và định dạng dọc
            clip = ImageClip(img_path).set_duration(duration_per_image)
            # Tự động resize/crop về chuẩn màn hình điện thoại
            clip = clip.resize(newsize=(1080, 1080)) # Resize cơ bản, bạn có thể chỉnh sâu hơn sau
            clips.append(clip)
            
        # Nối các đoạn ảnh lại thành 1 video liền mạch
        video_track = concatenate_videoclips(clips, method="compose")
        # Lồng ghép giọng đọc AI vào video
        final_video = video_track.set_audio(audio_clip)
        
        # Xuất file video hoàn chỉnh (Tự động tinh chỉnh thông số lách bản quyền nhẹ)
        final_video.write_videofile(
            output_video_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast" # Tăng tốc độ render cho server yếu
        )
        
        # Đóng các clip để giải phóng bộ nhớ RAM
        audio_clip.close()
        final_video.close()
        
    return output_video_path

# 2. Thiết kế Giao diện Web (UI hiển thị trên Safari của iPhone JB)
text_content = st.text_area("✍️ Nhập kịch bản / Văn bản tiếng Việt:", placeholder="Ví dụ: 3 mẹo giúp bạn kiếm tiền online hàng ngày...")
uploaded_files = st.file_uploader("🖼️ Chọn 3-5 bức ảnh nền cho video (JPG/PNG):", accept_multiple_files=True)

if st.button("🚀 BẮT ĐẦU TẠO VIDEO", type="primary"):
    if not text_content:
        st.error("Vui lòng không để trống phần kịch bản!")
    elif not uploaded_files:
        st.error("Vui lòng tải lên ít nhất 1 bức ảnh làm nền!")
    else:
        try:
            # Chạy hàm xử lý video
            final_mp4 = render_video(text_content, uploaded_files)
            
            st.success("🎉 Đã tạo video thành công!")
            
            # Hiển thị trình phát video lên màn hình web để xem thử
            with open(final_mp4, "rb") as video_file:
                video_bytes = video_file.read()
                st.video(video_bytes)
                
                # Nút bấm để tải video trực tiếp về iPhone
                st.download_button(
                    label="📥 TẢI VIDEO VỀ ĐIỆN THOẠI",
                    data=video_bytes,
                    file_name="mmo_automation_video.mp4",
                    mime="video/mp4"
                )
                
            # Dọn dẹp các file rác trong thư mục tạm sau khi render xong để tránh tràn ổ cứng
            files_to_clean = glob.glob(f"{TEMP_DIR}/*")
            for f in files_to_clean:
                if "final_output.mp4" not in f: # Giữ lại file gốc để người dùng tải
                    os.remove(f)
                    
        except Exception as e:
            st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {str(e)}")
